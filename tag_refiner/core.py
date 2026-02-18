"""コア処理モジュール"""
import random
import re
import shutil
from difflib import unified_diff
from pathlib import Path
from re import Pattern
from typing import Iterator

import typer

from .config import Config


# 正規表現メタ文字の判定用（要件: . + * などが含まれる場合のみ正規表現として扱う）
REGEX_META_CHAR_PATTERN = re.compile(r"[.\^$*+?{}\[\]\\|()]")


def resolve_read_source(file_path: Path, use_bak: bool) -> Path:
  """
  読み込み元ファイルを解決する（.bak優先）
  
  Args:
    file_path: 対象の .txt ファイル
    use_bak: .bak を優先するか
  
  Returns:
    Path: 実際に読み込むファイルパス
  """
  if not use_bak:
    return file_path

  backup_path = file_path.with_suffix(file_path.suffix + ".bak")
  if backup_path.exists():
    return backup_path

  return file_path


def load_add_tags(path: Path) -> list[str]:
  """
  追加タグファイルを読み込む
  
  Args:
    path: tag_add.txt のパス
    
  Returns:
    list[str]: 追加するタグのリスト
  """
  if not path.exists():
    typer.echo(f"警告: 追加タグファイルが見つかりません: {path}", err=True)
    return []
  
  tags = []
  try:
    with open(path, "r", encoding="utf-8") as f:
      for line in f:
        # コメントと空行を無視
        line = line.strip()
        if line and not line.startswith("#"):
          # カンマを削除してからタグを追加
          cleaned_tag = line.strip(',').strip()
          if cleaned_tag:
            tags.append(cleaned_tag)
  except Exception as e:
    typer.echo(f"警告: 追加タグファイルの読み込みに失敗: {e}", err=True)
    return []
  
  return tags


def load_remove_patterns(path: Path, use_regexp: bool) -> list[Pattern]:
  """
  削除パターンファイルを読み込む
  
  Args:
    path: tag_remove.txt のパス
    use_regexp: 正規表現を使用するかどうか
    
  Returns:
    list[Pattern]: 削除する正規表現パターンのリスト
    
  Raises:
    re.error: 正規表現のコンパイルに失敗した場合
  """
  if not path.exists():
    typer.echo(f"警告: 削除パターンファイルが見つかりません: {path}", err=True)
    return []
  
  patterns = []
  try:
    with open(path, "r", encoding="utf-8") as f:
      for line_num, line in enumerate(f, start=1):
        # コメントと空行を無視
        line = line.strip()
        if line and not line.startswith("#"):
          # regexp無効時は全て完全一致として扱う
          # regexp有効時でもメタ文字がない場合は完全一致として扱う
          use_regex_for_line = use_regexp and bool(REGEX_META_CHAR_PATTERN.search(line))

          if use_regex_for_line:
            try:
              pattern = re.compile(line)
            except re.error as e:
              typer.echo(f"エラー: 正規表現のコンパイルに失敗 ({path}:{line_num}): {e}", err=True)
              raise
          else:
            pattern = re.compile(rf"^{re.escape(line)}$")

          patterns.append(pattern)
  except re.error:
    raise
  except Exception as e:
    typer.echo(f"警告: 削除パターンファイルの読み込みに失敗: {e}", err=True)
    return []
  
  return patterns


def process_tags(
  tags: list[str],
  remove_patterns: list[Pattern],
  add_tags: list[str],
  shuffle: bool,
  shuffle_keep_first: int = 0,
) -> list[str]:
  """
  タグを処理する（削除、追加、シャッフル）
  
  Args:
    tags: 元のタグリスト
    remove_patterns: 削除パターン
    add_tags: 追加タグ
    shuffle: シャッフルするかどうか
    shuffle_keep_first: シャッフル時に先頭から固定する個数
    
  Returns:
    list[str]: 処理後のタグリスト
  """
  # 削除処理
  filtered_tags = []
  for tag in tags:
    should_remove = False
    for pattern in remove_patterns:
      if pattern.search(tag):
        should_remove = True
        break
    if not should_remove:
      filtered_tags.append(tag)
  
  # 追加処理：追加タグと同じものを既存タグから削除してから先頭に追加
  # 既存タグから追加タグと重複するものを削除
  for add_tag in add_tags:
    if add_tag in filtered_tags:
      filtered_tags.remove(add_tag)
  
  # 追加タグを先頭に追加（add_tagsの順序を保持）
  result_tags = add_tags + filtered_tags
  
  # シャッフル（先頭の指定個数は固定）
  if shuffle:
    keep_first = min(shuffle_keep_first, len(result_tags))
    fixed_tags = result_tags[:keep_first]
    shuffle_tags = result_tags[keep_first:]
    random.shuffle(shuffle_tags)
    result_tags = fixed_tags + shuffle_tags
  
  return result_tags


def generate_diff(before: str, after: str, filename: str = "file") -> str:
  """
  変更前後のdiffを生成する
  
  Args:
    before: 変更前の内容
    after: 変更後の内容
    filename: ファイル名（表示用）
    
  Returns:
    str: unified diff形式の差分
  """
  before_lines = before.splitlines(keepends=True)
  after_lines = after.splitlines(keepends=True)
  
  diff_lines = unified_diff(
    before_lines,
    after_lines,
    fromfile=f"before/{filename}",
    tofile=f"after/{filename}",
    lineterm="",
  )
  
  return "".join(diff_lines)


def create_backup(file_path: Path, config: Config) -> None:
  """
  バックアップファイルを作成する
  
  Args:
    file_path: バックアップ対象のファイル
    config: 設定
  """
  if not config.backup:
    return
  
  backup_path = file_path.with_suffix(file_path.suffix + ".bak")
  
  if config.backup_mode == "skip":
    if backup_path.exists():
      return
    shutil.copy2(file_path, backup_path)
  
  elif config.backup_mode == "overwrite":
    shutil.copy2(file_path, backup_path)
  
  elif config.backup_mode == "versioned":
    # .bak.1, .bak.2, ... の番号を探す
    version = 1
    while True:
      versioned_path = file_path.with_suffix(f"{file_path.suffix}.bak.{version}")
      if not versioned_path.exists():
        shutil.copy2(file_path, versioned_path)
        break
      version += 1


def refine_file(file_path: Path, config: Config, use_bak: bool = False) -> None:
  """
  単一のファイルを整形する
  
  Args:
    file_path: 対象ファイルのパス
    config: 設定
  """
  try:
    source_path = resolve_read_source(file_path, use_bak)

    # ファイル読み込み
    with open(source_path, "r", encoding="utf-8") as f:
      content = f.read().strip()
    
    # タグ分割とstrip
    tags = [tag.strip() for tag in content.split(",") if tag.strip()]
    
    # パターンとタグの読み込み
    remove_patterns = load_remove_patterns(config.tag_remove_file, config.regexp)
    add_tags = load_add_tags(config.tag_add_file)
    
    # タグ処理
    processed_tags = process_tags(
      tags, 
      remove_patterns, 
      add_tags, 
      config.shuffle,
      config.shuffle_keep_first,
    )
    
    # 出力形式: ", " で join
    new_content = ", ".join(processed_tags)
    
    # diff表示
    if config.diff:
      diff_output = generate_diff(content, new_content, file_path.name)
      if diff_output:
        typer.echo(f"\n=== {file_path} ===")
        typer.echo(diff_output)
    
    # dry_runの場合は変更しない
    if config.dry_run:
      typer.echo(f"[DRY RUN] {file_path}")
      return
    
    # 書き込み先の現在内容と同じ場合はスキップ
    try:
      with open(file_path, "r", encoding="utf-8") as f:
        current_target_content = f.read().strip()
      if current_target_content == new_content:
        return
    except Exception:
      # 現在内容が読めない場合は従来どおり書き込み処理へ進む
      pass
    
    # バックアップ作成
    create_backup(file_path, config)
    
    # ファイル書き込み
    with open(file_path, "w", encoding="utf-8") as f:
      f.write(new_content + "\n")
    
    typer.echo(f"処理完了: {file_path}")
  
  except Exception as e:
    typer.echo(f"エラー: {file_path} の処理に失敗しました: {e}", err=True)


def refine_directory(directory: Path, config: Config, use_bak: bool = False) -> None:
  """
  ディレクトリ内のファイルを整形する
  
  Args:
    directory: 対象ディレクトリのパス
    config: 設定
  """
  if not directory.exists():
    typer.echo(f"エラー: ディレクトリが見つかりません: {directory}", err=True)
    raise typer.Exit(code=1)
  
  if not directory.is_dir():
    typer.echo(f"エラー: パスがディレクトリではありません: {directory}", err=True)
    raise typer.Exit(code=1)
  
  # ファイル検索
  if config.recursive:
    files = list(directory.rglob("*.txt"))
  else:
    files = list(directory.glob("*.txt"))
  
  if not files:
    typer.echo(f"警告: .txtファイルが見つかりませんでした: {directory}", err=True)
    return
  
  typer.echo(f"{len(files)} 個のファイルを処理します...")
  
  # 各ファイルを処理
  for file_path in files:
    refine_file(file_path, config, use_bak=use_bak)
  
  typer.echo(f"\n完了: {len(files)} 個のファイルを処理しました")


def list_tags_in_directory(
  directory: Path,
  recursive: bool = False,
  show_count: bool = False,
  output_file: Path | None = None,
  sort_by: str = "tag",
  use_bak: bool = False,
) -> None:
  """
  ディレクトリ内のタグを収集して一覧表示する
  
  Args:
    directory: 対象ディレクトリのパス
    recursive: サブディレクトリを再帰的に処理
    show_count: 出現回数を表示
    output_file: 出力ファイルのパス（Noneの場合は標準出力）
    sort_by: 並び順（"count": 数の多い順、"tag": タグの名前順）
  """
  if not directory.exists():
    typer.echo(f"エラー: ディレクトリが見つかりません: {directory}", err=True)
    raise typer.Exit(code=1)
  
  if not directory.is_dir():
    typer.echo(f"エラー: パスがディレクトリではありません: {directory}", err=True)
    raise typer.Exit(code=1)
  
  # ファイル検索
  if recursive:
    files = list(directory.rglob("*.txt"))
  else:
    files = list(directory.glob("*.txt"))
  
  if not files:
    typer.echo(f"警告: .txtファイルが見つかりませんでした: {directory}", err=True)
    return
  
  # タグを収集
  tag_count: dict[str, int] = {}
  for file_path in files:
    try:
      source_path = resolve_read_source(file_path, use_bak)

      with open(source_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
      
      # タグ分割
      tags = [tag.strip() for tag in content.split(",") if tag.strip()]
      
      # カウント
      for tag in tags:
        tag_count[tag] = tag_count.get(tag, 0) + 1
    
    except Exception as e:
      typer.echo(f"警告: {file_path} の読み込みに失敗しました: {e}", err=True)
      continue
  
  if not tag_count:
    typer.echo("タグが見つかりませんでした", err=True)
    return
  
  # ソート
  if sort_by == "count":
    # 数の多い順（降順）、同じ数の場合はタグ名順
    sorted_tags = sorted(tag_count.items(), key=lambda x: (-x[1], x[0]))
  else:  # sort_by == "tag"
    # タグの名前順（昇順）
    sorted_tags = sorted(tag_count.items(), key=lambda x: x[0])
  
  # 出力内容を生成
  output_lines = []
  for tag, count in sorted_tags:
    if show_count:
      output_lines.append(f"{count}  {tag}")
    else:
      output_lines.append(tag)
  
  output_text = "\n".join(output_lines) + "\n"
  
  # 出力
  if output_file:
    try:
      with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_text)
      typer.echo(f"タグ一覧を {output_file} に出力しました（{len(tag_count)} 種類）")
    except Exception as e:
      typer.echo(f"エラー: ファイルへの書き込みに失敗しました: {e}", err=True)
      raise typer.Exit(code=1)
  else:
    # 標準出力
    typer.echo(output_text, nl=False)

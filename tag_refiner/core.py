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


def load_remove_patterns(path: Path) -> list[Pattern]:
  """
  削除パターンファイルを読み込む
  
  Args:
    path: tag_remove.txt のパス
    
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
          try:
            pattern = re.compile(line)
            patterns.append(pattern)
          except re.error as e:
            typer.echo(f"エラー: 正規表現のコンパイルに失敗 ({path}:{line_num}): {e}", err=True)
            raise
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


def refine_file(file_path: Path, config: Config) -> None:
  """
  単一のファイルを整形する
  
  Args:
    file_path: 対象ファイルのパス
    config: 設定
  """
  try:
    # ファイル読み込み
    with open(file_path, "r", encoding="utf-8") as f:
      content = f.read().strip()
    
    # タグ分割とstrip
    tags = [tag.strip() for tag in content.split(",") if tag.strip()]
    
    # パターンとタグの読み込み
    remove_patterns = load_remove_patterns(config.tag_remove_file)
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
    
    # 内容が変わっていない場合はスキップ
    if content == new_content:
      return
    
    # バックアップ作成
    create_backup(file_path, config)
    
    # ファイル書き込み
    with open(file_path, "w", encoding="utf-8") as f:
      f.write(new_content + "\n")
    
    typer.echo(f"処理完了: {file_path}")
  
  except Exception as e:
    typer.echo(f"エラー: {file_path} の処理に失敗しました: {e}", err=True)


def refine_directory(directory: Path, config: Config) -> None:
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
    refine_file(file_path, config)
  
  typer.echo(f"\n完了: {len(files)} 個のファイルを処理しました")

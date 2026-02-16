"""CLIエントリーポイント"""
from pathlib import Path
from typing import Optional

import typer

from .config import BackupMode, Config, load_config, merge_config
from .core import refine_directory

app = typer.Typer(
  name="tag-refiner",
  help="WD14 Danbooru形式のタグ整形CLIツール",
  add_completion=False,
)


@app.callback(invoke_without_command=True)
def main_callback(
  ctx: typer.Context,
  version: bool = typer.Option(
    False,
    "--version",
    "-v",
    help="バージョン情報を表示",
  ),
):
  """
  WD14 Danbooru形式のタグ整形CLIツール
  
  サブコマンドを指定してください:
  - refine: タグファイルを整形
  """
  if version:
    typer.echo("tag-refiner v1.0.0")
    raise typer.Exit()
  
  # サブコマンドが指定されていない場合はヘルプを表示
  if ctx.invoked_subcommand is None:
    typer.echo(ctx.get_help())
    raise typer.Exit()


@app.command(name="refine")
def refine(
  path: Optional[Path] = typer.Argument(
    None,
    help="処理対象のディレクトリパス（未指定の場合はconfigから取得）",
  ),
  recursive: Optional[bool] = typer.Option(
    None,
    "-r",
    "--recursive",
    help="サブディレクトリを再帰的に処理",
  ),
  shuffle: Optional[bool] = typer.Option(
    None,
    "--shuffle/--no-shuffle",
    help="タグの順序をランダム化",
  ),
  shuffle_keep_first: Optional[int] = typer.Option(
    None,
    "--shuffle-keep-first",
    help="シャッフル時に先頭から固定する個数（トリガーワード保護用）",
  ),
  backup: Optional[bool] = typer.Option(
    None,
    "--backup/--no-backup",
    help="バックアップファイルを作成",
  ),
  backup_mode: Optional[BackupMode] = typer.Option(
    None,
    "--backup-mode",
    help="バックアップモード",
  ),
  dry_run: bool = typer.Option(
    False,
    "--dry-run",
    help="実際にファイルを変更せず、処理内容のみ表示",
  ),
  diff: bool = typer.Option(
    False,
    "--diff",
    help="変更前後の差分を表示",
  ),
  add_file: Optional[Path] = typer.Option(
    None,
    "--add-file",
    help="追加タグファイルのパス",
  ),
  remove_file: Optional[Path] = typer.Option(
    None,
    "--remove-file",
    help="削除パターンファイルのパス",
  ),
  config_path: Optional[Path] = typer.Option(
    Path("config.json"),
    "--config",
    help="設定ファイルのパス",
  ),
  no_config: bool = typer.Option(
    False,
    "--no-config",
    help="設定ファイルを使用しない",
  ),
) -> None:
  """
  タグファイルを整形する
  """
  # 設定の読み込み
  if no_config:
    base_config = Config()
  else:
    # config_pathはデフォルト値があるのでNoneにはならない
    assert config_path is not None
    try:
      base_config = load_config(config_path)
    except FileNotFoundError:
      if config_path != Path("config.json"):
        # 明示的に指定された設定ファイルが見つからない場合はエラー
        typer.echo(f"エラー: 設定ファイルが見つかりません: {config_path}", err=True)
        raise typer.Exit(code=1)
      else:
        # デフォルトの設定ファイルが見つからない場合はデフォルト設定を使用
        base_config = Config()
    except Exception as e:
      typer.echo(f"エラー: 設定ファイルの読み込みに失敗: {e}", err=True)
      raise typer.Exit(code=1)
  
  # CLI引数でマージ（優先順位: CLI > config > default）
  config = merge_config(
    base_config,
    input_dir=path,
    recursive=recursive,
    tag_add_file=add_file,
    tag_remove_file=remove_file,
    shuffle=shuffle,
    shuffle_keep_first=shuffle_keep_first,
    backup=backup,
    backup_mode=backup_mode,
    dry_run=dry_run or base_config.dry_run,  # dry_runはTrueが優先
    diff=diff or base_config.diff,  # diffもTrueが優先
  )
  
  # ディレクトリ処理
  try:
    refine_directory(config.input_dir, config)
  except Exception as e:
    typer.echo(f"エラー: 処理中に問題が発生しました: {e}", err=True)
    raise typer.Exit(code=1)


def main():
  """エントリーポイント"""
  app()


if __name__ == "__main__":
  main()

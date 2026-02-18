"""設定管理モジュール"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional


BackupMode = Literal["skip", "overwrite", "versioned"]


@dataclass
class Config:
  """tag-refiner の設定"""
  
  input_dir: Path = field(default_factory=lambda: Path("./sample"))
  recursive: bool = False
  tag_add_file: Path = field(default_factory=lambda: Path("tag_add.txt"))
  tag_remove_file: Path = field(default_factory=lambda: Path("tag_remove.txt"))
  regexp: bool = False
  shuffle: bool = True
  shuffle_keep_first: int = 0  # シャッフル時に先頭から固定する個数
  backup: bool = True
  backup_mode: BackupMode = "skip"
  dry_run: bool = False
  diff: bool = False
  
  def __post_init__(self):
    """Path型への変換"""
    if not isinstance(self.input_dir, Path):
      self.input_dir = Path(self.input_dir)
    if not isinstance(self.tag_add_file, Path):
      self.tag_add_file = Path(self.tag_add_file)
    if not isinstance(self.tag_remove_file, Path):
      self.tag_remove_file = Path(self.tag_remove_file)


def load_config(config_path: Path) -> Config:
  """
  JSONファイルから設定を読み込む
  
  Args:
    config_path: 設定ファイルのパス
    
  Returns:
    Config: 読み込まれた設定
    
  Raises:
    FileNotFoundError: 設定ファイルが存在しない場合
    json.JSONDecodeError: JSONのパースに失敗した場合
  """
  if not config_path.exists():
    raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
  
  with open(config_path, "r", encoding="utf-8") as f:
    data = json.load(f)
  
  # Pathに変換
  if "input_dir" in data:
    data["input_dir"] = Path(data["input_dir"])
  if "tag_add_file" in data:
    data["tag_add_file"] = Path(data["tag_add_file"])
  if "tag_remove_file" in data:
    data["tag_remove_file"] = Path(data["tag_remove_file"])
  
  return Config(**data)


def merge_config(
  base: Config,
  input_dir: Optional[Path] = None,
  recursive: Optional[bool] = None,
  tag_add_file: Optional[Path] = None,
  tag_remove_file: Optional[Path] = None,
  regexp: Optional[bool] = None,
  shuffle: Optional[bool] = None,
  shuffle_keep_first: Optional[int] = None,
  backup: Optional[bool] = None,
  backup_mode: Optional[BackupMode] = None,
  dry_run: Optional[bool] = None,
  diff: Optional[bool] = None,
) -> Config:
  """
  CLI引数で設定をマージする（優先順位: CLI > config > default）
  
  Args:
    base: ベースとなる設定
    各パラメータ: CLI引数（Noneの場合はベース設定を使用）
    
  Returns:
    Config: マージされた設定
  """
  return Config(
    input_dir=input_dir if input_dir is not None else base.input_dir,
    recursive=recursive if recursive is not None else base.recursive,
    tag_add_file=tag_add_file if tag_add_file is not None else base.tag_add_file,
    tag_remove_file=tag_remove_file if tag_remove_file is not None else base.tag_remove_file,
    regexp=regexp if regexp is not None else base.regexp,
    shuffle=shuffle if shuffle is not None else base.shuffle,
    shuffle_keep_first=shuffle_keep_first if shuffle_keep_first is not None else base.shuffle_keep_first,
    backup=backup if backup is not None else base.backup,
    backup_mode=backup_mode if backup_mode is not None else base.backup_mode,
    dry_run=dry_run if dry_run is not None else base.dry_run,
    diff=diff if diff is not None else base.diff,
  )

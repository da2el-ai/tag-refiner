"""tag_refinerのテスト"""
import re
import tempfile
import unittest
from pathlib import Path

from tag_refiner.config import Config, merge_config
from tag_refiner.core import (
  load_add_tags,
  load_remove_patterns,
  process_tags,
  generate_diff,
)


class TestConfig(unittest.TestCase):
  """設定のテスト"""
  
  def test_config_default(self):
    """デフォルト設定のテスト"""
    config = Config()
    self.assertEqual(config.input_dir, Path("./sample"))
    self.assertFalse(config.recursive)
    self.assertTrue(config.shuffle)
    self.assertTrue(config.backup)
    self.assertEqual(config.backup_mode, "skip")
  
  def test_merge_config(self):
    """設定のマージテスト"""
    base = Config()
    merged = merge_config(
      base,
      input_dir=Path("./test"),
      recursive=True,
      shuffle=False,
    )
    self.assertEqual(merged.input_dir, Path("./test"))
    self.assertTrue(merged.recursive)
    self.assertFalse(merged.shuffle)
    # マージされていない設定はベースから継承
    self.assertTrue(merged.backup)


class TestProcessTags(unittest.TestCase):
  """タグ処理のテスト"""
  
  def test_process_tags_remove(self):
    """タグ削除のテスト"""
    tags = ["1girl", "blue hair", "background", "simple background"]
    patterns = [re.compile(r"^background$"), re.compile(r"^simple background$")]
    result = process_tags(tags, patterns, [], shuffle=False)
    self.assertNotIn("background", result)
    self.assertNotIn("simple background", result)
    self.assertIn("1girl", result)
    self.assertIn("blue hair", result)
  
  def test_process_tags_add(self):
    """タグ追加のテスト"""
    tags = ["1girl", "blue hair"]
    result = process_tags(tags, [], ["slim body", "detailed"], shuffle=False)
    self.assertIn("slim body", result)
    self.assertIn("detailed", result)
    self.assertEqual(len(result), 4)
    # 追加タグが先頭に配置されることを確認
    self.assertEqual(result[0], "slim body")
    self.assertEqual(result[1], "detailed")
  
  def test_process_tags_no_duplicate(self):
    """タグ重複防止のテスト"""
    tags = ["1girl", "blue hair"]
    result = process_tags(tags, [], ["1girl", "slim body"], shuffle=False)
    self.assertEqual(result.count("1girl"), 1)
    self.assertIn("slim body", result)
    # 追加タグが先頭、既存の1girlは削除されてから先頭に追加される
    self.assertEqual(result[0], "1girl")
    self.assertEqual(result[1], "slim body")
  
  def test_process_tags_shuffle_keep_first(self):
    """シャッフル時の先頭固定テスト"""
    tags = ["tag1", "tag2", "tag3", "tag4"]
    add_tags = ["add1", "add2"]
    
    # 先頭2個を固定してシャッフル
    result = process_tags(tags, [], add_tags, shuffle=True, shuffle_keep_first=2)
    
    # 先頭2個は常に add1, add2
    self.assertEqual(result[0], "add1")
    self.assertEqual(result[1], "add2")
    # 全長は6個
    self.assertEqual(len(result), 6)


class TestDiff(unittest.TestCase):
  """差分生成のテスト"""
  
  def test_generate_diff(self):
    """差分生成のテスト"""
    before = "1girl, blue hair, background"
    after = "1girl, blue hair, detailed"
    diff = generate_diff(before, after, "test.txt")
    self.assertIn("before/test.txt", diff)
    self.assertIn("after/test.txt", diff)
    self.assertIn("-1girl, blue hair, background", diff)
    self.assertIn("+1girl, blue hair, detailed", diff)


class TestLoadFiles(unittest.TestCase):
  """ファイル読み込みのテスト"""
  
  def test_load_add_tags(self):
    """追加タグ読み込みのテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
      tag_file = Path(tmpdir) / "tag_add.txt"
      tag_file.write_text("slim body\n# コメント\ndetailed\n\n", encoding="utf-8")
      
      tags = load_add_tags(tag_file)
      self.assertEqual(len(tags), 2)
      self.assertIn("slim body", tags)
      self.assertIn("detailed", tags)
      self.assertNotIn("# コメント", tags)
  
  def test_load_add_tags_with_comma(self):
    """カンマ付き追加タグのテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
      tag_file = Path(tmpdir) / "tag_add.txt"
      tag_file.write_text("slim body,\ndetailed,\n", encoding="utf-8")
      
      tags = load_add_tags(tag_file)
      self.assertEqual(len(tags), 2)
      # カンマが削除されていることを確認
      self.assertIn("slim body", tags)
      self.assertIn("detailed", tags)
      self.assertNotIn("slim body,", tags)
  
  def test_load_remove_patterns(self):
    """削除パターン読み込みのテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
      pattern_file = Path(tmpdir) / "tag_remove.txt"
      pattern_file.write_text("^background$\n# コメント\nlow quality\n", encoding="utf-8")
      
      patterns = load_remove_patterns(pattern_file)
      self.assertEqual(len(patterns), 2)
      self.assertTrue(any(p.pattern == "^background$" for p in patterns))
      self.assertTrue(any(p.pattern == "low quality" for p in patterns))
  
  def test_load_remove_patterns_invalid_regex(self):
    """不正な正規表現のテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
      pattern_file = Path(tmpdir) / "tag_remove.txt"
      pattern_file.write_text("^background$\n[invalid\n", encoding="utf-8")
      
      with self.assertRaises(re.error):
        load_remove_patterns(pattern_file)


if __name__ == "__main__":
  unittest.main()

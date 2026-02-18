# 📘 tag-refiner

WD14 (Danbooru形式) タグ整形CLIツール

## 概要

**tag-refiner** は機械学習用の画像タグファイルを整形するPython製CLIツールです。

### 主な機能

- ✨ 不要タグの削除（正規表現対応）
- ➕ 必要タグの追加
- 🔀 タグ順のランダム化
- 💾 安全なバックアップ
- 🔍 差分確認（dry-run / diff）

## インストール

```bash
# リポジトリをクローンする
git clone https://github.com/da2el-ai/tag-refiner.git
cd tag-refiner

python -m venv venv

# Macの場合
source venv/bin/activate
# Windowsの場合
venv\Scripts\activate

# 依存関係のインストール
pip install -e .
```

## 使い方

### 基本的な使い方

```bash
# 設定ファイルを使用して処理
tag-refiner refine ./sample

# dry-runで確認
tag-refiner refine ./sample --dry-run --diff

# 再帰的に処理
tag-refiner refine ./sample -r

# バージョン確認
tag-refiner --version
```

### サブコマンド

現在利用可能なサブコマンド：

- `refine`: タグファイルを整形

将来的に追加予定：

- `status`: タグの出現頻度統計など

### オプション

```
tag-refiner refine [PATH] [OPTIONS]

引数:
  PATH                      処理対象のディレクトリ（省略時はconfig.jsonから取得）

オプション:
  -r, --recursive          サブディレクトリを再帰的に処理
  --shuffle/--no-shuffle   タグの順序をランダム化
  --shuffle-keep-first N   シャッフル時に先頭からN個を固定（トリガーワード保護用）
  --backup/--no-backup     バックアップファイルを作成
  --backup-mode MODE       バックアップモード [skip|overwrite|versioned]
  --dry-run                実際にファイルを変更せず、処理内容のみ表示
  --diff                   変更前後の差分を表示
  --add-file PATH          追加タグファイルのパス
  --remove-file PATH       削除パターンファイルのパス
  --config PATH            設定ファイルのパス（デフォルト: config.json）
  --no-config              設定ファイルを使用しない
```

## 設定

### config.json

```json
{
  "input_dir": "./sample",
  "recursive": false,
  "tag_add_file": "tag_add.txt",
  "tag_remove_file": "tag_remove.txt",
  "shuffle": true,
  "shuffle_keep_first": 2,
  "backup": true,
  "backup_mode": "skip",
  "dry_run": false,
  "diff": false
}
```

- **input_dir**: 処理対象のディレクトリ
- **recursive**: `true` でサブディレクトリを再帰的に処理
- **tag_add_file**: 追加タグファイルのパス。デフォルトは `tag_add.txt`
- **tag_remove_file**: 除外タグファイルのパス。デフォルトは"`tag_remove.txt`
- **shuffle**: `true` でタグの順序をランダム化
- **shuffle_keep_first**: シャッフル時に先頭からN個を固定
  - 追加タグをトリガーワードとして使う場合、追加タグの個数を指定することで順序を固定できます
- **backup**: `true` でバックアップファイルを作成
- **backup_mode**: バックアップモード
  - skip: `.bak` が存在すれば作成しない
  - overwrite: 既存 `.bak` を上書き
  - versioned: `.bak.1`, `.bak.2` を作成
- **dry_run**: `true` で実際にファイルを変更せず、処理内容のみ表示
- **diff**: `true` で変更前後の差分を表示


### tag_add.txt

追加したいタグを1行に1つずつ記述します。

```text
# コメント
# 追加タグは必ず先頭に配置されます
# 末尾のカンマは自動的に削除されます
slim body
detailed background
```

**注意:**

- 追加タグは**必ず先頭に配置**されます
- 既存タグと重複する場合は、既存の位置から削除して先頭に移動します
- 末尾のカンマ（`slim body,`）は自動的に削除されます
- 複数回実行しても重複しません

### tag_remove.txt

削除したいタグのパターンを正規表現で1行に1つずつ記述します。

```text
# コメント
^background$
^simple background$
low quality
worst quality
```


## 開発

```bash
# 開発環境のセットアップ
python -m venv venv
source venv/bin/activate
pip install -e .

# テスト実行
pytest
```

## ライセンス

MIT License

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

現在利用可能なサブコマンド：

- `refine`: タグファイルを整形
- `list`: タグの一覧を出力

```bash
# タグファイルを整形
tag-refiner refine ./sample

# タグの一覧を表示
tag-refiner list ./sample

# バージョン確認
tag-refiner --version
```

### refineコマンド

タグファイルを整形します。

```bash
# 基本的な使い方
tag-refiner refine ./sample

# dry-runで確認
tag-refiner refine ./sample --dry-run --diff

# 再帰的に処理
tag-refiner refine ./sample -r
```

#### オプション

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
  --regexp/--no-regexp     除外タグで正規表現を使用
  --use-bak                キャプション読み込み時に .bak を優先使用
  --config PATH            設定ファイルのパス（デフォルト: config.json）
  --no-config              設定ファイルを使用しない
```

`--use-bak` を指定すると、各 `.txt` に対して読み込み元を `.txt.bak` → `.txt` の順で探索します。


### listコマンド

指定フォルダ内のキャプションファイルを開き、使われているタグの一覧を出力します。

```bash
# 基本的な使い方
tag-refiner list ./sample

# 出現回数を表示
tag-refiner list ./sample --list-count

# ファイルに出力
tag-refiner list ./sample --list-file tags.txt

# 出現回数順にソート
tag-refiner list ./sample --list-count --list-sort count

# 再帰的に処理
tag-refiner list ./sample -r
```

#### オプション

```
tag-refiner list PATH [OPTIONS]

引数:
  PATH                      処理対象のディレクトリ（必須）

オプション:
  -r, --recursive          サブディレクトリを再帰的に処理
  --list-count             出現回数を表示
  --list-file PATH         出力するファイル名（指定がなければ標準出力）
  --list-sort MODE         並び順 [tag|count]
                           tag: タグの名前順（デフォルト）
                           count: 数の多い順
  --use-bak                キャプション読み込み時に .bak を優先使用
```

`--use-bak` を指定すると、各 `.txt` に対して読み込み元を `.txt.bak` → `.txt` の順で探索します。

## 設定

### config.json

```json
{
  "input_dir": "./sample",
  "recursive": false,
  "tag_add_file": "tag_add.txt",
  "tag_remove_file": "tag_remove.txt",
  "regexp": false,
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
- **tag_remove_file**: 除外タグファイルのパス。デフォルトは `tag_remove.txt`
- **regexp**: `true` で除外タグに正規表現を使用
  - `false` の場合は全て完全一致
  - `true` の場合でも、メタ文字（例: `.`, `+`, `*`）がない行は完全一致
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

削除したいタグを1行に1つずつ記述します。

- `regexp: false` の場合: すべて完全一致で除外
- `regexp: true` の場合: メタ文字を含む行のみ正規表現、それ以外は完全一致

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

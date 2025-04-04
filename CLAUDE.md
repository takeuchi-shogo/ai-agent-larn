# CLAUDE.md

このファイルは、このリポジトリのコードを扱う際にClaude Code（claude.ai/code）に指針を提供します。

このリポジトリは、uvで管理されています。

AIの勉強用のリポジトリです。

それぞれのディレクトリでチャットボットを作成しています。

## ビルド/実行コマンド

- 環境構築: `uv venv`
- 依存関係のインストール: `uv pip install -e .`
- 依存関係の追加: `uv pip install <パッケージ名>`
- 開発用依存関係の追加: `uv pip install -D <パッケージ名>`
- メインアプリの実行: `uv run main.py`
- 単体テストの実行: `uv run pytest tests/path_to_test.py::test_name -v`
- 全テストの実行: `uv run pytest`
- 型チェック: `uv run mypy .`
- リンティング: `uv run ruff check .`
- コードフォーマット: `uv run ruff format .`

## コードスタイルガイドライン

- Python バージョン: >=3.13
- フォーマット: Black互換のフォーマット（ruffで強制）
- インポート: isort規約でソート、標準ライブラリ、サードパーティ、ローカルインポートをグループ
- 型: すべての関数パラメータと戻り値に型ヒントを使用
- 命名規則: 変数/関数にはsnake_case、クラスにはPascalCaseを使用
- ドキュメント文字列: すべての公開関数とクラスにGoogle形式のドキュメント文字列を使用
- エラー処理: 特定の例外を持つ明示的なtry/exceptブロックを使用
- ディレクトリ構造: 専用ディレクトリで機能/コンポーネント別に整理
- 行の長さ: 最大88文字

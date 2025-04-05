"""GraphRAGのコマンドラインインターフェース"""

import argparse
import os

from dotenv import load_dotenv

try:
    from graph_rag.rag_graph import GraphRAG
except ImportError:
    # 相対パスでのインポートを試みる
    from .rag_graph import GraphRAG

# 環境変数の読み込み
load_dotenv()


def main():
    """GraphRAGのCLIメイン関数"""
    parser = argparse.ArgumentParser(description="Neo4j GraphRAG CLI")
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # データロードコマンド
    load_parser = subparsers.add_parser("load", help="テキストデータをロード")
    load_parser.add_argument(
        "--file", "-f", required=True, help="ロードするテキストファイルのパス"
    )
    load_parser.add_argument(
        "--entity-type",
        "-t",
        default="Document",
        help="エンティティタイプ（デフォルト: Document）",
    )
    load_parser.add_argument(
        "--entity-id", "-i", required=True, help="エンティティID（一意の識別子）"
    )

    # 質問コマンド
    ask_parser = subparsers.add_parser("ask", help="GraphRAGに質問")
    ask_parser.add_argument("--question", "-q", required=True, help="質問文")
    ask_parser.add_argument(
        "--entity-id", "-i", required=True, help="参照するエンティティID"
    )
    ask_parser.add_argument(
        "--entity-type",
        "-t",
        default="Document",
        help="エンティティタイプ（デフォルト: Document）",
    )

    # クリアコマンド
    clear_parser = subparsers.add_parser("clear", help="データベースをクリア")

    args = parser.parse_args()

    # GraphRAGの初期化
    graph_rag = GraphRAG()

    try:
        if args.command == "load":
            # テキストデータのロード
            if not os.path.exists(args.file):
                print(f"エラー: ファイル '{args.file}' が見つかりません")
                return

            print(f"ファイル '{args.file}' をロード中...")
            graph_rag.load_text_to_graph(args.file, args.entity_type, args.entity_id)
            print("ロード完了")

        elif args.command == "ask":
            # 質問処理
            print(f"質問: {args.question}")
            response = graph_rag.ask(args.question)
            print("\n回答:")
            print(response)

        elif args.command == "clear":
            # データベースのクリア
            confirm = input(
                "警告: すべてのデータが削除されます。続行しますか？ (y/n): "
            )
            if confirm.lower() == "y":
                graph_rag.neo4j.clear_database()
                print("データベースをクリアしました")
            else:
                print("操作をキャンセルしました")

        else:
            parser.print_help()

    finally:
        # リソースの解放
        graph_rag.close()


if __name__ == "__main__":
    main()

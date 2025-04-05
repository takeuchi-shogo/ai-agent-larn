"""GraphRAGのメインモジュール"""

import argparse
import os

from dotenv import load_dotenv

try:
    from graph_rag.rag_graph import initialize_graph_rag
except ImportError:
    # 相対パスでのインポートを試みる
    from .rag_graph import initialize_graph_rag

# 環境変数の読み込み
load_dotenv()


def demonstrate_graph_rag(file_path: str = "data/hololive/sakura-miko.txt"):
    """GraphRAGのデモを実行する

    Args:
        file_path (str, optional): テキストファイルのパス
    """
    print("\n===== Neo4jを使用したGraphRAGのデモ =====\n")

    # GraphRAGの初期化
    print("\n1. GraphRAGの初期化とグラフデータベースの構築...")
    graph_rag = initialize_graph_rag(file_path, "VTuber", "sakura-miko")

    try:
        # テスト質問リスト
        test_questions = [
            "さくらみこの初のソロライブについて教えてください",
            "さくらみことホロライブの関係性を説明してください",
            "さくらみこの最近の活動について教えてください",
        ]

        print("\n2. GraphRAGを使用した質問応答のデモ\n")

        for i, question in enumerate(test_questions, 1):
            print(f"質問 {i}: {question}")
            response = graph_rag.ask(question)
            print(f"\n回答 {i}:\n{response}\n")
            print("-" * 70 + "\n")

        # 対話モード
        print("3. 対話モード（終了するには 'exit' または 'quit' と入力）\n")
        while True:
            user_question = input("質問を入力してください: ")
            if user_question.lower() in ["exit", "quit", "終了"]:
                break

            response = graph_rag.ask(user_question)
            print(f"\n回答:\n{response}\n")

    finally:
        # リソースの解放
        graph_rag.close()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="GraphRAGデモ")
    parser.add_argument(
        "--file",
        "-f",
        default="data/hololive/sakura-miko.txt",
        help="テキストファイルのパス",
    )

    args = parser.parse_args()
    file_path = args.file

    if not os.path.exists(file_path):
        print(f"エラー: ファイル '{file_path}' が見つかりません")
        return

    demonstrate_graph_rag(file_path)


if __name__ == "__main__":
    main()

"""
RAGデモンストレーション

このスクリプトは、単純なLLMとRAGの質問応答の違いを比較して表示します。
"""

import os
import sys

from rag.rag_chain import compare_llm_and_rag


def print_header(title: str) -> None:
    """タイトルヘッダーを表示する

    Args:
        title (str): 表示するタイトル
    """
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def run_demo() -> None:
    """RAGデモを実行する"""
    # さくらみこのデータファイルのパス
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "hololive",
        "sakura-miko.txt",
    )

    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"エラー: ファイル {file_path} が見つかりません。")
        sys.exit(1)

    # デモ開始
    print_header("RAG (Retrieval Augmented Generation) デモンストレーション")
    print("このデモでは、同じ質問に対する単純なLLMとRAGの回答の違いを比較します。")
    print("RAGは外部データソース（さくらみこに関する情報）を使用して回答を生成します。")
    print("一方、単純なLLMはモデルの訓練データのみに基づいて回答します。")

    # 質問のリスト
    questions = [
        "さくらみこの初のソロライブについて教えてください",
        "さくらみことSTARPHASEのボイスロイドとの関係は？",
        "さくらみことmiCometユニットについて教えてください",
        "さくらみこの2024年の活動について教えてください",
    ]

    # 各質問に対して比較を実行
    for i, question in enumerate(questions, 1):
        print_header(f"質問 {i}: {question}")

        print("比較処理中...\n")
        comparison = compare_llm_and_rag(question, file_path)

        print("--- 単純なLLM（外部データなし）の回答 ---\n")
        print(comparison["llm_response"])
        print("\n--- RAG（さくらみこデータ活用）の回答 ---\n")
        print(comparison["rag_response"])

        if i < len(questions):
            input("\nEnterキーを押して次の質問に進む...")

    print_header("デモ終了")
    print("以上がRAGと単純なLLMの比較デモです。")
    print(
        "RAGでは特定のドメイン（この場合はさくらみこに関する情報）に特化した回答ができるようになります。"
    )


if __name__ == "__main__":
    run_demo()

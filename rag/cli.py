"""
RAGを使用した質問応答のCLIツール
"""

import argparse
import time
from typing import Optional

from langchain_community.vectorstores import Qdrant

from rag.qdrant_db import QdrantManager, initialize_vectordb
from rag.rag_chain import ask_about_sakura_miko_with_rag


def check_vectordb_exists(collection_name: str = "sakura_miko_collection") -> bool:
    """ベクトルデータベースが存在するか確認する

    Args:
        collection_name (str, optional): コレクション名. デフォルトは"sakura_miko_collection"

    Returns:
        bool: ベクトルデータベースが存在する場合はTrue、そうでない場合はFalse
    """
    try:
        manager = QdrantManager(collection_name=collection_name)
        collections = manager.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        return collection_name in collection_names
    except:
        return False


def get_vectordb(collection_name: str = "sakura_miko_collection") -> Optional[Qdrant]:
    """既存のベクトルデータベースを取得する

    Args:
        collection_name (str, optional): コレクション名. デフォルトは"sakura_miko_collection"

    Returns:
        Optional[Qdrant]: ベクトルデータベースのインスタンス、存在しない場合はNone
    """
    if check_vectordb_exists(collection_name):
        manager = QdrantManager(collection_name=collection_name)
        return manager.get_vectorstore()
    return None


def main():
    """RAG CLIのメイン関数"""
    parser = argparse.ArgumentParser(
        description="さくらみこについてのRAGを使った質問応答"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="ベクトルデータベースを初期化します（データが既に存在する場合でも）",
    )
    parser.add_argument(
        "--file",
        type=str,
        default="/Users/takeuchishougo/dev-app/ai/ai-agent-larn/data/hololive/sakura-miko.txt",
        help="使用するデータファイルのパス",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="処理する質問（指定しない場合はインタラクティブモード）",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="sakura_miko_collection",
        help="使用するQdrantコレクション名",
    )

    args = parser.parse_args()

    # ベクトルデータベースの準備
    vectorstore = None
    if args.init or not check_vectordb_exists(args.collection):
        print(f"ベクトルデータベースを初期化中... ({args.file})")
        start_time = time.time()
        vectorstore = initialize_vectordb(args.file, collection_name=args.collection)
        elapsed_time = time.time() - start_time
        print(f"初期化完了 ({elapsed_time:.2f}秒)")
    else:
        print("既存のベクトルデータベースを使用します")
        vectorstore = get_vectordb(args.collection)

    # 質問処理
    if args.query:
        # 単一質問モード
        print(f"\n質問: {args.query}")
        print("\n回答処理中...\n")
        response = ask_about_sakura_miko_with_rag(args.query, vectorstore)
        print(response)
    else:
        # インタラクティブモード
        print("\nさくらみこについての質問応答システム")
        print("終了するには 'quit' または 'exit' と入力してください\n")

        while True:
            query = input("\n質問を入力してください: ")
            if query.lower() in ["quit", "exit", "終了"]:
                break

            print("\n回答処理中...\n")
            response = ask_about_sakura_miko_with_rag(query, vectorstore)
            print(response)


if __name__ == "__main__":
    main()

"""
ベクトルデータベース(Qdrant)を使用したRAG実装のためのモジュール
"""

import os
from typing import List

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# 環境変数の読み込み
load_dotenv()

# APIキーの存在確認
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables")


class QdrantManager:
    """Qdrantベクトルデータベースを管理するクラス"""

    def __init__(
        self,
        collection_name: str = "sakura_miko_collection",
        host: str = "localhost",
        port: int = 6333,
    ) -> None:
        """Qdrantマネージャーの初期化

        Args:
            collection_name (str, optional): コレクション名. デフォルトは"sakura_miko_collection"
            host (str, optional): ホスト名. デフォルトは"localhost"
            port (int, optional): ポート番号. デフォルトは6333
        """
        self.collection_name = collection_name
        self.client = QdrantClient(host=host, port=port)
        self.embeddings = OpenAIEmbeddings()

    def create_collection(self, vector_size: int = 1536) -> None:
        """ベクトルコレクションを作成する

        Args:
            vector_size (int, optional): ベクトルのサイズ. デフォルトは1536 (OpenAI ada-002モデル)
        """
        # コレクションが存在するか確認
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]

        # コレクションが存在しない場合のみ作成
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            print(f"コレクション '{self.collection_name}' を作成しました")
        else:
            print(f"コレクション '{self.collection_name}' は既に存在します")

    def load_and_split_documents(
        self, file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[Document]:
        """ドキュメントをロードして分割する

        Args:
            file_path (str): ドキュメントのパス
            chunk_size (int, optional): チャンクサイズ. デフォルトは1000
            chunk_overlap (int, optional): チャンク間のオーバーラップサイズ. デフォルトは200

        Returns:
            List[Document]: 分割されたドキュメントのリスト
        """
        # テキストファイルをロード
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()

        # テキストを分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        print(f"{len(chunks)} チャンクに分割しました")
        return chunks

    def index_documents(self, documents: List[Document]) -> None:
        """ドキュメントをインデックス化する

        Args:
            documents (List[Document]): インデックス化するドキュメントのリスト
        """
        # ドキュメントをQdrantにインデックス化
        Qdrant.from_documents(
            documents,
            self.embeddings,
            url="http://localhost:6333",
            collection_name=self.collection_name,
        )
        print(f"{len(documents)} チャンクをインデックス化しました")

    def get_vectorstore(self) -> Qdrant:
        """ベクトルストアのインスタンスを取得する

        Returns:
            Qdrant: ベクトルストアのインスタンス
        """
        return Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings,
        )


def initialize_vectordb(
    file_path: str,
    collection_name: str = "sakura_miko_collection",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> Qdrant:
    """ベクトルデータベースを初期化し、ドキュメントをインデックス化する

    Args:
        file_path (str): ドキュメントのファイルパス
        collection_name (str, optional): コレクション名. デフォルトは"sakura_miko_collection"
        chunk_size (int, optional): チャンクサイズ. デフォルトは1000
        chunk_overlap (int, optional): チャンク間のオーバーラップサイズ. デフォルトは200

    Returns:
        Qdrant: ベクトルストアのインスタンス
    """
    # Qdrantマネージャーの初期化
    manager = QdrantManager(collection_name=collection_name)

    # コレクションの作成
    manager.create_collection()

    # ドキュメントのロードと分割
    documents = manager.load_and_split_documents(
        file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    # ドキュメントのインデックス化
    manager.index_documents(documents)

    # ベクトルストアのインスタンスを返す
    return manager.get_vectorstore()


if __name__ == "__main__":
    # 初期化とインデックス作成をテスト
    initialize_vectordb(
        file_path="/Users/takeuchishougo/dev-app/ai/ai-agent-larn/data/hololive/sakura-miko.txt"
    )

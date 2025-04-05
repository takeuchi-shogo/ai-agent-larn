"""
さくらみこの最新情報を処理するクエリプロセッサ

既存のQdrantとNeo4jデータを使用して、さくらみこに関する最新情報の質問に回答します。
"""

import os
from typing import Dict, Optional, Tuple

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

try:
    from graph_rag import Neo4jManager, GraphRAG
except ImportError:
    # 相対パスでのインポート
    from .neo4j_graph import Neo4jManager
    from .rag_graph import GraphRAG


# 環境変数の読み込み
load_dotenv()

# APIキーの存在確認
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables")


class MikoQueryProcessor:
    """さくらみこに関する質問を処理するクラス"""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_username: str = "neo4j",
        neo4j_password: str = "password",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "sakura_miko_collection",
        model_name: str = "gpt-3.5-turbo",
    ):
        """クエリプロセッサを初期化する

        Args:
            neo4j_uri (str, optional): Neo4jデータベースのURI
            neo4j_username (str, optional): Neo4jデータベースのユーザー名
            neo4j_password (str, optional): Neo4jデータベースのパスワード
            qdrant_host (str, optional): QdrantサーバーのHOST
            qdrant_port (int, optional): QdrantサーバーのPORT
            collection_name (str, optional): Qdrantコレクション名
            model_name (str, optional): 使用するモデル名
        """
        self.neo4j = Neo4jManager(neo4j_uri, neo4j_username, neo4j_password)
        self.graph_rag = GraphRAG(
            neo4j_uri=neo4j_uri,
            neo4j_username=neo4j_username,
            neo4j_password=neo4j_password,
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            collection_name=collection_name,
            model_name=model_name,
        )
        self.llm = ChatOpenAI(model_name=model_name, temperature=0)

    def verify_data_exists(self, entity_type: str = "VTuber", entity_id: str = "sakura-miko") -> bool:
        """データが既にNeo4jに存在するか検証する

        Args:
            entity_type (str, optional): エンティティの種類
            entity_id (str, optional): エンティティID

        Returns:
            bool: データが存在すればTrue
        """
        query = f"""
        MATCH (e:{entity_type} {{id: $entity_id}})
        RETURN count(e) AS count
        """
        try:
            result = self.neo4j.execute_query(query, {"entity_id": entity_id})
            return result[0]["count"] > 0
        except Exception as e:
            print(f"データ検証エラー: {e}")
            return False

    def get_latest_info(self, query: str = "さくらみこについての最新情報を教えて") -> str:
        """さくらみこに関する最新情報を取得する

        Args:
            query (str, optional): 質問文。デフォルトは「さくらみこについての最新情報を教えて」

        Returns:
            str: 質問への回答
        """
        try:
            # 既存データを確認
            if not self.verify_data_exists():
                return "さくらみこに関するデータがデータベースに見つかりませんでした。"

            # GraphRAGでの回答を取得
            response = self.graph_rag.ask(query)
            return response
        except Exception as e:
            return f"エラーが発生しました: {e}"

    def validate_info_accuracy(self, info: str) -> Tuple[bool, str]:
        """LLMを使用して情報の正確性を検証する

        Args:
            info (str): 検証する情報

        Returns:
            Tuple[bool, str]: (情報が正確であるかの判定, 判定の理由)
        """
        validate_prompt = ChatPromptTemplate.from_template(
            """
            以下の情報はさくらみこ（ホロライブVTuber）に関する記述です。
            この情報の正確性を検証し、明らかな誤りや矛盾がないかを判断してください。

            情報:
            {info}

            判定結果を以下の形式で返してください:
            正確性: [高い/中程度/低い]
            理由: [理由の説明]
            修正すべき点: [ある場合は修正点]
            """
        )

        response = self.llm.invoke(validate_prompt.format(info=info))
        
        # 応答から正確性を抽出
        accuracy_level = "低い"
        if "正確性: 高い" in response.content:
            accuracy_level = "高い"
            is_accurate = True
        elif "正確性: 中程度" in response.content:
            accuracy_level = "中程度"
            is_accurate = True
        else:
            is_accurate = False

        return is_accurate, response.content

    def process_miko_query(self, query: str = "さくらみこについての最新情報を教えて") -> Dict[str, str]:
        """さくらみこに関する質問を処理し、結果と検証を返す

        Args:
            query (str, optional): 質問文

        Returns:
            Dict[str, str]: 処理結果の辞書
        """
        # 情報を取得
        info = self.get_latest_info(query)
        
        # 情報の正確性を検証
        is_accurate, validation_details = self.validate_info_accuracy(info)
        
        return {
            "query": query,
            "response": info,
            "is_accurate": is_accurate,
            "validation": validation_details
        }

    def close(self):
        """リソースを解放する"""
        if hasattr(self, "neo4j"):
            self.neo4j.close()
        if hasattr(self, "graph_rag"):
            self.graph_rag.close()


def get_miko_latest_info(query: str = "さくらみこについての最新情報を教えて") -> Dict[str, str]:
    """さくらみこに関する最新情報を取得し、その正確性を検証する関数

    Args:
        query (str, optional): 質問文

    Returns:
        Dict[str, str]: 処理結果の辞書
    """
    processor = None
    try:
        processor = MikoQueryProcessor()
        result = processor.process_miko_query(query)
        return result
    except Exception as e:
        return {
            "query": query,
            "response": f"エラーが発生しました: {e}",
            "is_accurate": False,
            "validation": "エラーのため検証できませんでした"
        }
    finally:
        if processor:
            processor.close()


if __name__ == "__main__":
    # 単体テスト用
    result = get_miko_latest_info()
    print(f"質問: {result['query']}")
    print(f"\n回答:\n{result['response']}")
    print(f"\n正確性: {'高い' if result['is_accurate'] else '低い'}")
    print(f"\n検証詳細:\n{result['validation']}")
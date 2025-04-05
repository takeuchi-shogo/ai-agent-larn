"""GraphRAGを実装するモジュール"""

import os
from typing import List, Set, Tuple

from dotenv import load_dotenv

try:
    from graph_rag.neo4j_graph import Neo4jManager
except ImportError:
    # 相対パスでのインポートを試みる
    from .neo4j_graph import Neo4jManager

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from rag.qdrant_db import QdrantManager

# 環境変数の読み込み
load_dotenv()

# APIキーの存在確認
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables")


class GraphRAG:
    """GraphRAGを実装するクラス"""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_username: str = "neo4j",
        neo4j_password: str = "password",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "sakura_miko_collection",
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.0,
    ) -> None:
        """GraphRAGを初期化します。

        Args:
            neo4j_uri (str, optional): Neo4jデータベースのURI
            neo4j_username (str, optional): Neo4jデータベースのユーザー名
            neo4j_password (str, optional): Neo4jデータベースのパスワード
            qdrant_host (str, optional): Qdrantサーバーのホスト名
            qdrant_port (int, optional): Qdrantサーバーのポート番号
            collection_name (str, optional): Qdrantコレクション名
            model_name (str, optional): 使用するLLMモデル名
            temperature (float, optional): 生成の温度
        """
        # Neo4jマネージャーの初期化
        self.neo4j = Neo4jManager(neo4j_uri, neo4j_username, neo4j_password)

        # Qdrantマネージャーの初期化
        self.qdrant = QdrantManager(
            collection_name=collection_name, host=qdrant_host, port=qdrant_port
        )

        # LLMの初期化
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)

        # コレクションの作成確認
        self.qdrant.create_collection()

        # RAGチェーンのキャッシュ
        self._rag_chain = None

    def load_text_to_graph(
        self, file_path: str, entity_type: str, entity_id: str
    ) -> None:
        """テキストファイルをロードしてグラフデータベースとベクトルDBに格納する

        Args:
            file_path (str): テキストファイルのパス
            entity_type (str): エンティティの種類
            entity_id (str): エンティティのID
        """
        # テキストファイルの読み込み
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()

        # 基本的なメタデータを抽出し、エンティティノードを作成
        entity_properties = {"source": file_path, "title": os.path.basename(file_path)}
        self.neo4j.create_entity_node(entity_type, entity_id, entity_properties)

        # テキストをチャンクに分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, length_function=len
        )
        chunks = text_splitter.split_documents(documents)

        print(f"テキストを {len(chunks)} チャンクに分割しました")

        # チャンクをベクトルDBに格納し、Neo4jにChunkノードを作成
        for i, chunk in enumerate(chunks):
            chunk_id = f"{entity_id}_chunk_{i}"
            chunk.metadata["chunk_id"] = chunk_id
            chunk.metadata["entity_id"] = entity_id
            chunk.metadata["entity_type"] = entity_type

            # Neo4jにChunkノードを作成
            self.neo4j.create_entity_node(
                "Chunk",
                chunk_id,
                {
                    "content": chunk.page_content,
                    "index": i,
                    "source": file_path,
                },
            )

            # ChunkとEntityの関係を作成
            self.neo4j.create_relationship(
                "Chunk", chunk_id, entity_type, entity_id, "PART_OF"
            )

        # ベクトルストアにチャンクをインデックス化
        self.qdrant.index_documents(chunks)
        print(f"{len(chunks)} チャンクをインデックス化しました")

        # エンティティの情報を抽出する
        self._extract_entities_from_chunks(chunks, entity_id, entity_type)

    def _extract_entities_from_chunks(
        self, chunks: List[Document], parent_entity_id: str, parent_entity_type: str
    ) -> None:
        """チャンクからエンティティ情報を抽出してグラフに追加する

        Args:
            chunks (List[Document]): テキストチャンクのリスト
            parent_entity_id (str): 親エンティティID
            parent_entity_type (str): 親エンティティタイプ
        """
        # エンティティ抽出プロンプト
        extract_prompt = ChatPromptTemplate.from_template(
            """
            あなたはテキストから重要なエンティティ（人物、場所、組織、イベントなど）を抽出する専門家です。
            以下のテキストから主要なエンティティとその関係を抽出してください。

            テキスト:
            {text}

            親エンティティID: {parent_id}
            親エンティティタイプ: {parent_type}

            以下のJSON形式で結果を返してください：
            {{
                "entities": [
                    {{
                    "id": "一意のID",
                    "type": "Person/Organization/Event/Place など",
                    "name": "エンティティの名前",
                    "properties": {{"key1": "value1", "key2": "value2"}}
                    }}
                ],
                "relationships": [
                    {{
                        "source_id": "元のエンティティID",
                        "target_id": "関連エンティティID",
                        "type": "関係の種類（所属、参加、開催など）",
                        "properties": {{"key1": "value1"}}
                    }}
                ]
            }}

            注意:
            - 抽出するエンティティは5つ以内に制限し、本当に重要なものだけを選択してください
            - IDは英数字とハイフンのみを含む一意の識別子にしてください
            - 親エンティティとの関係も必ず含めてください
            - プロパティは情報が明確な場合のみ含めてください
            - 客観的な事実のみを抽出し、推測は避けてください
            """
        )

        # JSONパース用関数
        def safe_json_parse(text):
            try:
                # 必要に応じてJSON文字列を抽出する処理
                import json
                import re

                # テキストからJSONブロックを抽出
                json_match = re.search(r"```json\s*(.+?)\s*```", text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = text

                data = json.loads(json_str)
                return data
            except Exception as e:
                print(f"JSON解析エラー: {e}")
                return {"entities": [], "relationships": []}

        # 処理済みエンティティとリレーションシップの追跡
        processed_entities: Set[str] = set()
        processed_relationships: Set[Tuple[str, str, str]] = set()

        # 各チャンクに対してエンティティ抽出を実行
        for chunk in chunks:
            response = self.llm.invoke(
                extract_prompt.format(
                    text=chunk.page_content,
                    parent_id=parent_entity_id,
                    parent_type=parent_entity_type,
                )
            )

            # 応答をJSONとして解析
            data = safe_json_parse(response.content)

            # エンティティを追加
            for entity in data.get("entities", []):
                entity_id = entity.get("id")
                entity_type = entity.get("type")
                properties = entity.get("properties", {})

                # 名前をプロパティに追加
                if "name" in entity:
                    properties["name"] = entity["name"]

                # 重複を避ける
                if entity_id not in processed_entities:
                    self.neo4j.create_entity_node(entity_type, entity_id, properties)
                    processed_entities.add(entity_id)

            # 関係を追加
            for rel in data.get("relationships", []):
                source_id = rel.get("source_id")
                target_id = rel.get("target_id")
                rel_type = rel.get("type")
                rel_properties = rel.get("properties", {})

                # ソースとターゲットのタイプを取得
                source_type = (
                    parent_entity_type if source_id == parent_entity_id else "UNKNOWN"
                )
                target_type = (
                    parent_entity_type if target_id == parent_entity_id else "UNKNOWN"
                )

                # データベースから不明なエンティティタイプを取得
                if source_type == "UNKNOWN" or target_type == "UNKNOWN":
                    for entity in data.get("entities", []):
                        if entity.get("id") == source_id and source_type == "UNKNOWN":
                            source_type = entity.get("type")
                        if entity.get("id") == target_id and target_type == "UNKNOWN":
                            target_type = entity.get("type")

                # 重複を避ける
                rel_key = (source_id, target_id, rel_type)
                if rel_key not in processed_relationships:
                    try:
                        self.neo4j.create_relationship(
                            source_type,
                            source_id,
                            target_type,
                            target_id,
                            rel_type,
                            rel_properties,
                        )
                        processed_relationships.add(rel_key)
                    except Exception as e:
                        print(f"関係作成エラー: {e}")

    def create_rag_chain(self, k: int = 5):
        """RAGチェーンを作成する

        Args:
            k (int, optional): 検索する類似ドキュメントの数. デフォルトは5

        Returns:
            Chain: 実行可能なRAGチェーン
        """
        if self._rag_chain is not None:
            return self._rag_chain

        # ベクトルストアを取得
        vectorstore = self.qdrant.get_vectorstore()

        # 検索コンポーネントの設定
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})

        # ドキュメントフォーマット関数
        def format_docs(docs: List[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in docs)

        # グラフ検索関数
        def search_graph(question: str) -> str:
            # 質問からキーエンティティを抽出
            extract_entities_prompt = ChatPromptTemplate.from_template(
                """
                以下の質問から検索キーワードとなる主要なエンティティを抽出してください：
                
                質問: {question}
                
                結果は以下の形式でJSON形式で返してください：
                ```json
                {{
                  "keywords": ["キーワード1", "キーワード2", ...],
                  "entity_types": ["検索すべきエンティティタイプ1", "タイプ2", ...]
                }}
                ```
                
                entity_typesには「VTuber」「Event」「Organization」などの適切なタイプを含めてください。
                最も関連性の高いものを2-3項目選んでください。
                """
            )

            response = self.llm.invoke(
                extract_entities_prompt.format(question=question)
            )
            extracted_data = safe_json_parse(response.content)

            # Neo4jでエンティティを検索
            keywords = extracted_data.get("keywords", [])
            entity_types = extracted_data.get("entity_types", [])

            graph_results = []

            # キーワードによる検索
            if keywords:
                keyword_query = """
                MATCH (n)
                WHERE any(keyword IN $keywords WHERE toLower(toString(n.name)) CONTAINS toLower(keyword))
                       OR any(keyword IN $keywords WHERE toLower(toString(n.id)) CONTAINS toLower(keyword))
                RETURN n.id AS id, labels(n) AS types, properties(n) AS properties
                LIMIT 5
                """
                keyword_results = self.neo4j.execute_query(
                    keyword_query, {"keywords": keywords}
                )
                graph_results.extend(keyword_results)

            # エンティティタイプによる検索
            if entity_types:
                type_conditions = [f"'{t}' IN labels(n)" for t in entity_types]
                type_query = f"""
                MATCH (n)
                WHERE {" OR ".join(type_conditions)}
                RETURN n.id AS id, labels(n) AS types, properties(n) AS properties
                LIMIT 5
                """
                type_results = self.neo4j.execute_query(type_query)
                graph_results.extend(type_results)

            # 結果を整形
            if graph_results:
                formatted_results = []
                for result in graph_results:
                    entity_id = result.get("id")
                    entity_types = result.get("types")
                    properties = result.get("properties")

                    # 整形された結果に追加
                    formatted_result = f"エンティティID: {entity_id}\n"
                    formatted_result += f"タイプ: {', '.join(entity_types)}\n"
                    formatted_result += "プロパティ:\n"
                    for key, value in properties.items():
                        if key != "content":  # contentプロパティは大きすぎるので除外
                            formatted_result += f"  {key}: {value}\n"

                    # 関連ノードも検索
                    related_entities = self.neo4j.query_related_entities(
                        entity_types[0], entity_id
                    )
                    if related_entities:
                        formatted_result += "関連エンティティ:\n"
                        for rel_entity in related_entities:
                            rel_id = rel_entity.get("id")
                            rel_types = rel_entity.get("types")
                            rel_type = rel_entity.get("relationship_type")
                            formatted_result += (
                                f"  {rel_id} ({rel_types[0]}) - {rel_type}関係\n"
                            )

                    formatted_results.append(formatted_result)

                return "\n\n".join(formatted_results)
            else:
                return "グラフデータベースから関連情報は見つかりませんでした。"

        # プロンプトテンプレートの定義
        template = """
        あなたはさくらみこについて詳しく答えるアシスタントです。

        以下の情報源を使用して質問に最善を尽くして答えてください。

        グラフデータベースからの情報：
        {graph_info}

        類似テキストチャンク：
        {context}

        質問: {question}

        回答に情報源から引用した部分があれば「(情報源より)」と明記してください。
        情報源にない情報については「情報源にはこの情報がありません」と正直に伝えてください。
        回答は日本語で簡潔に、かつ十分な情報量を含めるようにしてください。
        """

        # プロンプトの作成
        prompt = ChatPromptTemplate.from_template(template)

        # 出力パーサー
        output_parser = StrOutputParser()

        # JSON解析ヘルパー関数
        def safe_json_parse(text):
            try:
                import json
                import re

                # テキストからJSONブロックを抽出
                json_match = re.search(r"```json\s*(.+?)\s*```", text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = text

                data = json.loads(json_str)
                return data
            except Exception as e:
                print(f"JSON解析エラー: {e}")
                return {"keywords": [], "entity_types": ["VTuber", "Event"]}

        # RAGチェーンの構築
        self._rag_chain = (
            {
                "graph_info": lambda x: search_graph(x["question"]),
                "context": lambda x: format_docs(retriever.invoke(x["question"])),
                "question": lambda x: x["question"],
            }
            | prompt
            | self.llm
            | output_parser
        )

        return self._rag_chain

    def ask(self, question: str) -> str:
        """GraphRAGを使用して質問に回答する

        Args:
            question (str): 質問文

        Returns:
            str: 回答
        """
        # RAGチェーンの作成（またはキャッシュから取得）
        chain = self.create_rag_chain()

        # 質問の処理
        response = chain.invoke({"question": question})

        return response

    def close(self) -> None:
        """リソースを解放する"""
        if hasattr(self, "neo4j") and self.neo4j is not None:
            self.neo4j.close()


def initialize_graph_rag(file_path: str, entity_type: str, entity_id: str) -> GraphRAG:
    """GraphRAGを初期化しデータをロードする

    Args:
        file_path (str): テキストファイルのパス
        entity_type (str): メインエンティティのタイプ
        entity_id (str): メインエンティティのID

    Returns:
        GraphRAG: 初期化されたGraphRAGインスタンス
    """
    # GraphRAGの初期化
    graph_rag = GraphRAG()

    # データのロード
    graph_rag.load_text_to_graph(file_path, entity_type, entity_id)

    return graph_rag


if __name__ == "__main__":
    # データファイルのパス
    file_path = (
        "/Users/takeuchishougo/dev-app/ai/ai-agent-larn/data/hololive/sakura-miko.txt"
    )

    # GraphRAGの初期化
    graph_rag = initialize_graph_rag(file_path, "VTuber", "sakura-miko")

    try:
        # テスト質問
        test_questions = [
            "さくらみこの最初のソロライブはいつどこで開催されましたか？",
            "さくらみこと星街すいせいの関係について教えてください",
            "さくらみこはどのようなゲームが好きですか？",
        ]

        for question in test_questions:
            print(f"\n質問: {question}")
            response = graph_rag.ask(question)
            print(f"回答: {response}\n")
            print("-" * 50)

    finally:
        # リソースの解放
        graph_rag.close()

"""Neo4jグラフデータベースを管理するモジュール"""

from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

# 環境変数の読み込み
load_dotenv()


class Neo4jManager:
    """Neo4jグラフデータベースを管理するクラス"""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
    ) -> None:
        """Neo4jデータベースマネージャーを初期化します。

        Args:
            uri (str, optional): Neo4jデータベースのURI。
                デフォルトは"bolt://localhost:7687"。
            username (str, optional): Neo4jデータベースのユーザー名。
                デフォルトは"neo4j"。
            password (str, optional): Neo4jデータベースのパスワード。
                デフォルトは"password"。
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        try:
            self.driver.verify_connectivity()
            print("Neo4jデータベースに接続しました")
        except ServiceUnavailable:
            print(
                "Neo4jデータベースに接続できません。サービスが利用可能か確認してください。"
            )
            raise

    def close(self) -> None:
        """Neo4jデータベース接続を閉じる"""
        if self.driver is not None:
            self.driver.close()
            print("Neo4jデータベース接続を閉じました")

    def create_entity_node(
        self, entity_type: str, entity_id: str, properties: Dict[str, Any]
    ) -> None:
        """エンティティノードを作成する

        Args:
            entity_type (str): エンティティの種類 (Person, Event, Organization など)
            entity_id (str): エンティティの一意のID
            properties (Dict[str, Any]): エンティティのプロパティ
        """
        with self.driver.session() as session:
            # エンティティタイプのスペースをアンダースコアに置き換える
            safe_entity_type = entity_type.replace(" ", "_")

            properties_str = ", ".join([f"{key}: ${key}" for key in properties.keys()])
            query = f"""
            MERGE (e:{safe_entity_type} {{id: $entity_id, {properties_str}}})
            RETURN e
            """

            params = {"entity_id": entity_id, **properties}
            session.run(query, params)
            print(f"{safe_entity_type} ノード '{entity_id}' を作成しました")

    def create_relationship(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """ノード間の関係を作成する

        Args:
            source_type (str): 始点ノードの種類
            source_id (str): 始点ノードのID
            target_type (str): 終点ノードの種類
            target_id (str): 終点ノードのID
            relationship_type (str): 関係の種類
            properties (Optional[Dict[str, Any]], optional): 関係のプロパティ
        """
        if properties is None:
            properties = {}

        with self.driver.session() as session:
            # エンティティタイプのスペースをアンダースコアに置き換える
            safe_source_type = source_type.replace(" ", "_")
            safe_target_type = target_type.replace(" ", "_")

            properties_str = ", ".join([f"{key}: ${key}" for key in properties.keys()])
            relationship_props = ""
            if properties_str:
                relationship_props = f" {{{properties_str}}}"

            query = f"""
            MATCH (a:{safe_source_type} {{id: $source_id}})
            MATCH (b:{safe_target_type} {{id: $target_id}})
            MERGE (a)-[r:{relationship_type}{relationship_props}]->(b)
            RETURN r
            """

            params = {"source_id": source_id, "target_id": target_id, **properties}
            session.run(query, params)
            print(
                f"'{source_id}'({source_type}) と '{target_id}'({target_type}) の間に "
                f"'{relationship_type}' 関係を作成しました"
            )

    def query_related_entities(
        self, entity_type: str, entity_id: str, relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """特定のエンティティに関連するエンティティを検索する

        Args:
            entity_type (str): エンティティの種類
            entity_id (str): エンティティのID
            relationship_type (Optional[str], optional): 関係の種類（指定しない場合はすべての関係）

        Returns:
            List[Dict[str, Any]]: 関連エンティティのリスト
        """
        with self.driver.session() as session:
            # エンティティタイプのスペースをアンダースコアに置き換える
            safe_entity_type = entity_type.replace(" ", "_")

            if relationship_type:
                query = f"""
                MATCH (a:{safe_entity_type} {{id: $entity_id}})-[r:{relationship_type}]->(b)
                RETURN b.id AS id, labels(b) AS types, properties(b) AS properties,
                       type(r) AS relationship_type, properties(r) AS relationship_properties
                UNION
                MATCH (a)-[r:{relationship_type}]->(b:{safe_entity_type} {{id: $entity_id}})
                RETURN a.id AS id, labels(a) AS types, properties(a) AS properties,
                       type(r) AS relationship_type, properties(r) AS relationship_properties
                """
            else:
                query = f"""
                MATCH (a:{safe_entity_type} {{id: $entity_id}})-[r]->(b)
                RETURN b.id AS id, labels(b) AS types, properties(b) AS properties,
                       type(r) AS relationship_type, properties(r) AS relationship_properties
                UNION
                MATCH (a)-[r]->(b:{safe_entity_type} {{id: $entity_id}})
                RETURN a.id AS id, labels(a) AS types, properties(a) AS properties,
                       type(r) AS relationship_type, properties(r) AS relationship_properties
                """

            result = session.run(query, {"entity_id": entity_id})
            entities = [record for record in result]
            return entities

    def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """カスタムクエリを実行する

        Args:
            query (str): Cypherクエリ
            params (Optional[Dict[str, Any]], optional): クエリパラメータ

        Returns:
            List[Dict[str, Any]]: クエリ結果
        """
        if params is None:
            params = {}

        with self.driver.session() as session:
            result = session.run(query, params)
            return [record.data() for record in result]

    def clear_database(self) -> None:
        """データベースのすべてのノードと関係を削除する"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("データベースをクリアしました")


if __name__ == "__main__":
    # 接続テスト
    manager = Neo4jManager()
    try:
        # テストデータの作成
        manager.clear_database()

        # VTuberノードを作成
        manager.create_entity_node(
            "VTuber",
            "sakura-miko",
            {
                "name": "さくらみこ",
                "english_name": "Sakura Miko",
                "group": "ホロライブ",
                "generation": "0期生",
                "debut_date": "2018-08-01",
            },
        )

        # イベントノードを作成
        manager.create_entity_node(
            "Event",
            "first-live",
            {
                "name": 'さくらみこ1st Live "flower fantasista!"',
                "date": "2024-10-26",
                "venue": "有明アリーナ",
            },
        )

        # 関係を作成
        manager.create_relationship(
            "VTuber", "sakura-miko", "Event", "first-live", "PERFORMED_AT"
        )

        # 関連エンティティを検索
        entities = manager.query_related_entities("VTuber", "sakura-miko")
        print("関連エンティティ:", entities)

    finally:
        manager.close()

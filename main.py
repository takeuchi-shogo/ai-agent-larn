# GraphRAGのインポート
from graph_rag.query_processor import get_miko_latest_info
from lang_graph.chat_graph import create_chat_graph
from lang_graph.decision_graph import create_decision_graph
from lang_graph.simple_graph import create_simple_graph
from rag.qdrant_db import initialize_vectordb
from rag.rag_chain import ask_about_sakura_miko_with_rag
from rag.simple_llm import ask_about_sakura_miko

# LangChainのインポートはコメントアウト
# from lang_chain.chains import create_simple_chain
# from lang_chain.agents import create_agent


def demonstrate_langchain_simple_chain():
    """シンプルなLangChainチェーンのデモを実行"""
    # chain = create_simple_chain()
    # result = chain.invoke({"question": "AIの未来について簡潔に教えてください"})
    # print("==== シンプルチェーンの結果 ====")
    # print(result)
    # print()
    pass


def demonstrate_langchain_agent():
    """LangChainエージェントのデモを実行"""
    # agent_executor = create_agent()
    # result = agent_executor.invoke({"input": "2025年の10月1日は何曜日ですか？また、1234 × 5678の計算結果も教えてください"})
    # print("==== エージェントの結果 ====")
    # print(result["output"])
    # print()
    pass


def demonstrate_simple_langgraph():
    """シンプルなLangGraphのデモを実行"""
    graph = create_simple_graph()
    result = graph.invoke({"question": "AIとヒトの協調について簡潔に教えてください"})
    print("==== シンプルLangGraphの結果 ====")
    print(result["response"])
    print()


def demonstrate_decision_langgraph():
    """決定グラフのデモを実行"""
    graph = create_decision_graph()
    result = graph.invoke(
        {
            "question": "2025年の7月の最初の月曜日は何日ですか？また、7890 × 1234の計算結果も教えてください"
        }
    )
    print("==== 決定LangGraphの結果 ====")
    print(result["final_answer"])
    print()
    print("思考プロセス:", result["thought"])
    print("計画:", result["plan"])
    print("ツール出力:", result["tools_output"])
    print()


def demonstrate_chat_langgraph():
    """チャットグラフのデモを実行"""
    graph = create_chat_graph()
    messages = [{"role": "user", "content": "AIの応用事例について教えてください"}]
    result = graph.invoke({"messages": messages, "context": {}})
    print("==== チャットLangGraphの結果 ====")
    for msg in result["messages"]:
        role = "ユーザー" if msg["role"] == "user" else "アシスタント"
        print(f"{role}: {msg['content']}")
    print()


def demonstrate_simple_llm():
    """RAGなしの単純なLLMのデモを実行"""
    result = ask_about_sakura_miko()
    print("==== RAGなしの単純なLLMの結果 ====")
    print("質問: さくらみこについて最近の動向を日付を添えて教えてください")
    print("\n回答:")
    print(result)
    print()


def demonstrate_rag():
    """RAGを使った質問応答のデモを実行"""
    vectorstore = initialize_vectordb("data/hololive/sakura-miko.txt")
    result = ask_about_sakura_miko_with_rag(
        "さくらみこの配信活動について教えてください", vectorstore
    )
    print("==== RAGの結果 ====")
    print(result)
    print()


def setup_graph_rag():
    """GraphRAGのデータベースをセットアップし、インスタンスを返す"""
    file_path = "data/hololive/sakura-miko.txt"
    entity_type = "VTuber"
    entity_id = "sakura-miko"

    # Neo4jマネージャーを直接初期化
    from graph_rag import GraphRAG, Neo4jManager

    # Neo4jマネージャーの初期化
    neo4j = Neo4jManager()

    try:
        # データベースが既に存在するか確認
        query = f"""
        MATCH (e:{entity_type} {{id: $entity_id}})
        RETURN count(e) AS count
        """
        result = neo4j.execute_query(query, {"entity_id": entity_id})

        # GraphRAGインスタンスの作成
        graph_rag = GraphRAG()

        # データが存在しない場合のみロードする
        if result[0]["count"] == 0:
            print("\nデータのロードとグラフの構築を行っています...")
            graph_rag.load_text_to_graph(file_path, entity_type, entity_id)
            print("データのロードが完了しました")
        else:
            print("\n既存のグラフデータを使用します")

        return graph_rag
    except Exception as e:
        print(f"GraphRAGのセットアップエラー: {e}")
        if neo4j:
            neo4j.close()
        return None


def demonstrate_graph_rag():
    """GraphRAGのデモを実行"""
    print("\n==== GraphRAGのデモ ====")
    print("Neo4jとQdrantを組み合わせたGraphRAGを使用します")

    # GraphRAGのセットアップ（既存データの再利用）
    graph_rag = setup_graph_rag()

    if not graph_rag:
        print("GraphRAGの初期化に失敗しました")
        return

    try:
        # テスト質問
        test_questions = [
            "さくらみこの初のソロライブについて教えてください",
            "さくらみことホロライブの関係について教えてください",
            "さくらみこの最近の活動について教えてください",
        ]

        for i, question in enumerate(test_questions, 1):
            print(f"\n質問 {i}: {question}")
            response = graph_rag.ask(question)
            print(f"\n回答 {i}:\n{response}")
            print("-" * 50)

    finally:
        # リソースの解放
        if graph_rag:
            graph_rag.close()

    print()


def demonstrate_miko_latest_info():
    """さくらみこの最新情報を取得し検証するデモを実行"""
    print("\n==== さくらみこ最新情報クエリ処理のデモ ====")
    print("既存のNeo4jとQdrantデータを使用し、情報の正確性を検証します")

    # デフォルトクエリ
    query = "さくらみこについての最新情報を教えて"

    print(f"\n質問: {query}")
    result = get_miko_latest_info(query)

    print("\n回答:")
    print(result["response"])

    print("\n情報の正確性検証:")
    print(f"正確性: {'高い' if result['is_accurate'] else '低い'}")
    print("\n検証詳細:")
    print(result["validation"])

    print("-" * 50)
    print()


def main():
    """メイン関数: 各デモを実行"""
    print("AIエージェントと言語モデルのデモを開始します！\n")

    # 各種デモの実行
    # コメント/コメント解除して実行するデモを選択できます

    # LangGraphのデモ
    # demonstrate_simple_langgraph()
    # demonstrate_decision_langgraph()
    # demonstrate_chat_langgraph()

    # RAGなしの単純なLLMのデモ
    # demonstrate_simple_llm()

    # LangChainのデモ
    # demonstrate_langchain_simple_chain()
    # demonstrate_langchain_agent()

    # RAGのデモ
    # demonstrate_rag()

    # GraphRAGのデモ
    # demonstrate_graph_rag()

    # さくらみこ最新情報クエリのデモ
    demonstrate_miko_latest_info()

    print("デモが完了しました！")


if __name__ == "__main__":
    main()

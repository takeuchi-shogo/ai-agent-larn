from lang_graph.chat_graph import create_chat_graph
from lang_graph.decision_graph import create_decision_graph
from lang_graph.simple_graph import create_simple_graph
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
    demonstrate_simple_llm()

    # LangChainのデモ
    # demonstrate_langchain_simple_chain()
    # demonstrate_langchain_agent()

    print("デモが完了しました！")


if __name__ == "__main__":
    main()

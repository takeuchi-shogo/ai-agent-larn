from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph


class SimpleState(TypedDict):
    """シンプルなグラフの状態"""

    question: str
    response: str


def create_simple_graph(model_name="gpt-3.5-turbo", temperature=0.7):
    """シンプルなLangGraphを作成する

    Args:
        model_name (str, optional): 使用するモデル名. デフォルトは"gpt-3.5-turbo".
        temperature (float, optional): 生成の温度. デフォルトは0.7.

    Returns:
        Runnable: 実行可能なグラフ
    """
    # モデルの設定
    llm = ChatOpenAI(model_name=model_name, temperature=temperature)

    # プロンプトテンプレート
    prompt = ChatPromptTemplate.from_template(
        "あなたは優秀なAIアシスタントです。次の質問に簡潔に答えてください: {question}"
    )

    # ノード関数の定義
    def generate_response(state: SimpleState) -> SimpleState:
        """応答を生成するノード"""
        question = state["question"]
        response = prompt.invoke({"question": question}) | llm
        return {"question": question, "response": response.content}

    # グラフの構築
    workflow = StateGraph(SimpleState)
    workflow.add_node("generate_response", generate_response)
    workflow.set_entry_point("generate_response")
    workflow.set_finish_point("generate_response")

    # コンパイル
    compiled_graph = workflow.compile()

    return compiled_graph

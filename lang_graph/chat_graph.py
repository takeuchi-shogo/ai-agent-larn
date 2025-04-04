from typing import Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph


class Message(TypedDict):
    """チャットメッセージ"""

    role: str
    content: str


class ChatState(TypedDict):
    """チャットグラフの状態"""

    messages: List[Message]
    context: Optional[Dict[str, Any]]


def create_chat_graph(model_name="gpt-3.5-turbo", temperature=0.7):
    """会話を処理するLangGraphを作成する

    Args:
        model_name (str, optional): 使用するモデル名. デフォルトは"gpt-3.5-turbo".
        temperature (float, optional): 生成の温度. デフォルトは0.7.

    Returns:
        Runnable: 実行可能なグラフ
    """
    # モデルの設定
    llm = ChatOpenAI(model_name=model_name, temperature=temperature)

    # プロンプトテンプレート
    system_prompt = """あなたは優秀なAIアシスタントです。以下のガイドラインに従ってください：
    
    1. ユーザーの質問に対して正確かつ簡潔に回答してください。
    2. 質問に答えられない場合は、正直にわからないと伝えてください。
    3. 必要に応じて、コンテキスト情報を活用してください。
    4. 回答は簡潔に、しかし十分な情報を含むようにしてください。
    5. 丁寧で親しみやすい口調を保ってください。
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("placeholder", "{messages}")]
    )

    # ノード関数の定義
    def generate_response(state: ChatState) -> ChatState:
        """応答を生成するノード"""
        messages = state["messages"]

        # プロンプトに入れるメッセージの形式に変換
        prompt_messages = []
        for msg in messages:
            if msg["role"] == "user":
                prompt_messages.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                prompt_messages.append(("ai", msg["content"]))
            elif msg["role"] == "system":
                # システムメッセージはスキップ（すでにプロンプトに含まれている）
                continue

        # 応答の生成
        response = prompt.invoke({"messages": prompt_messages}) | llm

        # 新しいメッセージを追加
        new_messages = messages + [{"role": "assistant", "content": response.content}]

        return {"messages": new_messages, "context": state.get("context")}

    def should_continue(state: ChatState) -> Literal["continue", "end"]:
        """会話を継続すべきか判断するノード"""
        # 最後のメッセージがアシスタントからであれば終了
        if state["messages"] and state["messages"][-1]["role"] == "assistant":
            return "end"
        return "continue"

    # グラフの構築
    workflow = StateGraph(ChatState)
    workflow.add_node("generate_response", generate_response)

    # エントリーポイントとエッジの設定
    workflow.set_entry_point("generate_response")
    workflow.add_conditional_edges(
        "generate_response",
        should_continue,
        {"continue": "generate_response", "end": END},
    )

    # コンパイル
    compiled_graph = workflow.compile()

    return compiled_graph

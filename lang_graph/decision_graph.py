from typing import List, Literal, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode


# ツールの定義
@tool
def search_database(query: str) -> str:
    """データベースから情報を検索する"""
    # 実際にはデータベース検索API呼び出し
    return f"'{query}'の検索結果: データベースから取得した情報がここに表示されます。"


@tool
def calculate(expression: str) -> float:
    """数式の計算を行う"""
    return eval(expression)


class DecisionState(TypedDict):
    """決定グラフの状態"""

    question: str
    thought: str
    plan: List[str]
    current_step: int
    tools_output: List[str]
    final_answer: str


def create_decision_graph(model_name="gpt-3.5-turbo", temperature=0.7):
    """ツールを使った決定グラフを作成する

    Args:
        model_name (str, optional): 使用するモデル名. デフォルトは"gpt-3.5-turbo".
        temperature (float, optional): 生成の温度. デフォルトは0.7.

    Returns:
        Runnable: 実行可能なグラフ
    """
    # モデルの設定
    llm = ChatOpenAI(model_name=model_name, temperature=temperature)

    # ツールの設定
    tools = [search_database, calculate]
    tool_node = ToolNode(tools)

    # プロンプトとノード関数の定義
    planner_prompt = ChatPromptTemplate.from_template(
        """あなたは問題解決エキスパートです。与えられた質問に答えるための計画を立ててください。
        
        質問: {question}
        
        必要に応じて以下のツールを使用できます:
        - search_database: データベースから情報を検索する
        - calculate: 数式の計算を行う
        
        次の形式で出力してください:
        思考: [問題解決の思考プロセス]
        計画: [実行すべきステップのリスト]
        """
    )

    def plan(state: DecisionState) -> DecisionState:
        """計画を立てるノード"""
        question = state["question"]
        response = planner_prompt.invoke({"question": question}) | llm
        content = response.content

        # 出力からthoughtとplanを抽出
        thought = ""
        plan = []

        for line in content.split("\n"):
            if line.startswith("思考:"):
                thought = line[3:].strip()
            elif line.startswith("計画:"):
                plan_text = line[3:].strip()
                plan = [step.strip() for step in plan_text.strip("[]").split(",")]

        return {
            "question": question,
            "thought": thought,
            "plan": plan,
            "current_step": 0,
            "tools_output": [],
            "final_answer": "",
        }

    tool_prompt = ChatPromptTemplate.from_template(
        """与えられた計画のステップに基づいて、適切なツールを使用してください。
        
        質問: {question}
        計画: {plan}
        現在のステップ: {current_step}
        現在のステップの内容: {current_step_content}
        これまでのツール出力: {tools_output}
        
        次のツールの入力を<tool>ツール名:入力</tool>の形式で出力してください。
        例: <tool>search_database:人工知能の歴史</tool>
        例: <tool>calculate:1234*5678</tool>
        """
    )

    def prepare_tool(state: DecisionState) -> dict:
        """ツールの使用を準備するノード"""
        current_step = state["current_step"]
        current_step_content = (
            state["plan"][current_step] if current_step < len(state["plan"]) else ""
        )

        response = (
            tool_prompt.invoke(
                {
                    "question": state["question"],
                    "plan": state["plan"],
                    "current_step": current_step + 1,  # 1ベースの表記に
                    "current_step_content": current_step_content,
                    "tools_output": state["tools_output"],
                }
            )
            | llm
        )

        content = response.content

        # ツール指定を抽出
        import re

        tool_match = re.search(r"<tool>(.*?):(.*?)</tool>", content)

        if tool_match:
            tool_name = tool_match.group(1).strip()
            tool_input = tool_match.group(2).strip()
            return {"tool_name": tool_name, "tool_input": tool_input}
        else:
            # ツールが指定されなかった場合、最終回答へ
            return {"skip_tool": True}

    synthesizer_prompt = ChatPromptTemplate.from_template(
        """これまでに収集した情報に基づいて、質問に対する最終的な回答を提供してください。
        
        質問: {question}
        思考プロセス: {thought}
        計画: {plan}
        ツール出力: {tools_output}
        
        質問に対する最終的な回答を提供してください。
        """
    )

    def synthesize_answer(state: DecisionState) -> DecisionState:
        """最終回答を合成するノード"""
        response = (
            synthesizer_prompt.invoke(
                {
                    "question": state["question"],
                    "thought": state["thought"],
                    "plan": state["plan"],
                    "tools_output": state["tools_output"],
                }
            )
            | llm
        )

        return {**state, "final_answer": response.content}

    def after_tool_use(state: DecisionState, tool_output: str) -> DecisionState:
        """ツール使用後の状態更新"""
        new_tools_output = state["tools_output"] + [tool_output]
        new_current_step = state["current_step"] + 1

        return {
            **state,
            "tools_output": new_tools_output,
            "current_step": new_current_step,
        }

    def should_continue(state: DecisionState) -> Literal["continue", "finish"]:
        """継続すべきか判断するノード"""
        if state["current_step"] >= len(state["plan"]):
            return "finish"
        return "continue"

    # グラフの構築
    workflow = StateGraph(DecisionState)

    workflow.add_node("plan", plan)
    workflow.add_node("prepare_tool", prepare_tool)
    workflow.add_node("tool", tool_node)
    workflow.add_node("synthesize", synthesize_answer)

    # エッジの設定
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "prepare_tool")

    # prepare_toolからの分岐
    workflow.add_conditional_edges(
        "prepare_tool",
        lambda x: "finish" if x.get("skip_tool") else "continue",
        {"continue": "tool", "finish": "synthesize"},
    )

    # ツール使用後の処理
    workflow.add_edge("tool", "prepare_tool", after_tool_use)

    # 終了条件
    workflow.add_conditional_edges(
        "prepare_tool", should_continue, {"continue": "tool", "finish": "synthesize"}
    )

    workflow.set_finish_point("synthesize")

    # コンパイル
    compiled_graph = workflow.compile()

    return compiled_graph

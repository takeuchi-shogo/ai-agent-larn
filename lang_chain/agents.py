from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


@tool
def search(query: str) -> str:
    """検索エンジンから情報を取得する"""
    # 実際には検索APIを呼び出す
    return f"'{query}'の検索結果: 関連情報がこちらに表示されます"


@tool
def calculator(expression: str) -> float:
    """数学の計算を実行する"""
    return eval(expression)


def create_agent(model_name="gpt-4o-mini-2024-07-18", temperature=0.7):
    """LangChainエージェントを作成する

    Args:
        model_name (str, optional): 使用するモデル名. デフォルトは"gpt-4o-mini-2024-07-18".
        temperature (float, optional): 生成の温度. デフォルトは0.7.

    Returns:
        AgentExecutor: 実行可能なエージェント
    """
    # 使用するツール定義
    tools = [search, calculator]

    # エージェント用のプロンプト
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "あなたは役立つAIアシスタントです。ユーザーの質問に答えるために、必要に応じてツールを使用してください。",
            ),
            ("human", "{input}"),
        ]
    )

    # LLMモデルの定義
    llm = ChatOpenAI(model_name=model_name, temperature=temperature)

    # エージェントの作成
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return agent_executor

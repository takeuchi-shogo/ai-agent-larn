import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from ai_agent.multi_llm_agent.base_agent import BaseAgent

load_dotenv()


class OpenAIAgent(BaseAgent):
    """
    OpenAIのモデルを使用したエージェント実装。
    """

    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        """
        OpenAIAgentを初期化します。

        Args:
            model_name: 使用するOpenAIモデル。デフォルトはgpt-4o-mini。
            temperature: 生成の温度パラメータ。
        """
        super().__init__(model_name, temperature)
        self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません。")

        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model_name=self.model_name,
            temperature=self.temperature,
        )
        self.agent_executor = None

    def setup(self, system_prompt: str, tools: Optional[List[BaseTool]] = None) -> None:
        """
        エージェントをセットアップします。

        Args:
            system_prompt: エージェントのシステムプロンプト。
            tools: エージェントに提供するツールのリスト。
        """
        if tools:
            self.tools = tools

        # システムプロンプトを拡張
        enhanced_system_prompt = f"""
{system_prompt}

重要なルール:
1. 同じ検索クエリを2回以上実行しないでください
2. 十分な情報が集まったら、すぐに最終回答に進んでください
3. 検索結果は要約して活用してください
4. 最大2回のツール使用で結論を出してください
"""

        # プロンプトテンプレートの作成
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", enhanced_system_prompt + "\n\n{agent_scratchpad}"),
                ("human", "{input}"),
            ]
        )

        # エージェントの作成
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)

        # エージェントエグゼキューターの設定
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=3,  # 最大反復回数を3回に制限
            return_intermediate_steps=True,  # 中間ステップを返すように設定
        )

    def run(self, query: str) -> Dict[str, Any]:
        """
        クエリに対してエージェントを実行します。

        Args:
            query: ユーザーからのクエリ。

        Returns:
            エージェントの応答を含む辞書。
        """
        if not self.agent_executor:
            raise ValueError(
                "エージェントがセットアップされていません。setup()メソッドを先に呼び出してください。"
            )

        try:
            result = self.agent_executor.invoke({"input": query})
            return result
        except Exception as e:
            # エラーが発生した場合やタイムアウトした場合でも
            # 中間結果を含む部分的な結果を返す
            if hasattr(self.agent_executor, "intermediate_steps"):
                return {
                    "error": str(e),
                    "intermediate_steps": self.agent_executor.intermediate_steps,
                }
            return {"error": str(e)}

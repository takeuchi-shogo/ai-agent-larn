import os
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_gemini_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI

from ai_agent.multi_llm_agent.base_agent import BaseAgent


class GeminiAgent(BaseAgent):
    """
    Google Geminiモデルを使用したエージェント実装。
    """

    def __init__(self, model_name: str = "gemini-pro", temperature: float = 0.7):
        """
        GeminiAgentを初期化します。

        Args:
            model_name: 使用するGeminiモデル。デフォルトはgemini-pro。
            temperature: 生成の温度パラメータ。
        """
        super().__init__(model_name, temperature)
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY環境変数が設定されていません。")
            
        self.llm = ChatGoogleGenerativeAI(
            api_key=self.api_key,
            model=self.model_name,
            temperature=self.temperature
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
        
        # プロンプトテンプレートの作成
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt
                ),
                ("human", "{input}"),
                ("assistant", "{agent_scratchpad}"),
            ]
        )
        
        # エージェントの作成
        agent = create_gemini_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True
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
            raise ValueError("エージェントがセットアップされていません。setup()メソッドを先に呼び出してください。")
        
        return self.agent_executor.invoke({"input": query})
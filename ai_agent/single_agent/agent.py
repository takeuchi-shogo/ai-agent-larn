import os
from typing import Any, Dict

import requests
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


class SingleAgent:
    """
    Web検索とYouTube検索を実行できるシンプルなAIエージェント。
    """

    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        """
        SingleAgentを初期化します。

        Args:
            model_name: 使用するOpenAIモデル。
            temperature: モデルの温度パラメータ。
        """
        # 検索ツールの初期化
        self.search_tool = DuckDuckGoSearchRun()

        # ツールリストの作成
        self.tools = [self.search_tool, self.youtube_search]

        # システムプロンプトの作成
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたはホロライブのVTuber「さくらみこ」の情報を提供する専門アシスタントです。"
                    "一般的な情報が必要な場合は検索ツールを使用し、ユーザーが動画を探している場合は"
                    "YouTube検索ツールを使用してください。「さくらみこ」に関連する情報や最新の活動、"
                    "配信、コラボ情報などを優先的に提供してください。\n\n"
                    "{agent_scratchpad}",
                ),
                ("human", "{input}"),
            ]
        )

        # LLMの作成
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)

        # エージェントの作成
        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent, tools=self.tools, verbose=True
        )

    @tool
    def youtube_search(self, query: str) -> str:
        """
        クエリに関連するYouTubeビデオを検索します。

        Args:
            query: YouTube検索クエリ。

        Returns:
            YouTube検索結果をフォーマットした文字列。
        """
        # 環境変数からAPIキーを取得
        api_key = os.environ.get("YOUTUBE_API_KEY")

        if not api_key:
            return "YouTube APIキーが見つかりません。YOUTUBE_API_KEY環境変数を設定してください。"

        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "key": api_key,
            "maxResults": 5,
            "type": "video",
        }

        try:
            response = requests.get(url, params=params)
            results = response.json()

            # 結果のフォーマット
            output = "YouTube検索結果:\n"
            for item in results.get("items", []):
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                channel = item["snippet"]["channelTitle"]
                output += f"- {title} by {channel}\n  https://www.youtube.com/watch?v={video_id}\n"

            return output
        except Exception as e:
            return f"YouTube検索中にエラーが発生しました: {str(e)}"

    def run(self, query: str) -> Dict[str, Any]:
        """
        指定されたクエリでエージェントを実行します。

        Args:
            query: ユーザーのクエリ。

        Returns:
            エージェントの応答。
        """
        return self.agent_executor.invoke({"input": query})


if __name__ == "__main__":
    # 使用例
    agent = SingleAgent()
    result = agent.run("さくらみこの最新情報を教えてください")
    print(result["output"])

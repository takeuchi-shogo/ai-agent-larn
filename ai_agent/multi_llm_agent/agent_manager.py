from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool, tool

from ai_agent.multi_llm_agent.claude_agent import ClaudeAgent
from ai_agent.multi_llm_agent.gemini_agent import GeminiAgent
from ai_agent.multi_llm_agent.openai_agent import OpenAIAgent


class AgentRole(Enum):
    """
    マルチエージェント環境での各エージェントの役割を定義します。
    """

    RESEARCHER = auto()  # 情報収集と検索を担当
    ANALYZER = auto()  # データ分析と評価を担当
    CREATOR = auto()  # コンテンツ生成とアイデア創出を担当


class MultiLLMAgentManager:
    """
    複数のLLMエージェント（OpenAI、Claude、Gemini）を管理し、
    タスクを分配して結果を集約するマネージャークラス。
    """

    def __init__(self):
        """
        MultiLLMAgentManagerを初期化し、使用するエージェントをセットアップします。
        """
        # 共通のツールを初期化
        self.search_tool = DuckDuckGoSearchRun()
        self.common_tools = [self.search_tool, self.youtube_search]

        # 各エージェントの初期化
        self.openai_agent = OpenAIAgent(model_name="gpt-4o-mini")
        self.claude_agent = ClaudeAgent()
        self.gemini_agent = GeminiAgent()

        # 役割に応じたエージェントのセットアップ
        self._setup_agents()

    def _setup_agents(self) -> None:
        """
        各エージェントを役割に応じてセットアップします。
        """
        # OpenAI: リサーチャー役割
        researcher_prompt = """
        あなたはホロライブのVTuber「さくらみこ」に関する情報収集のスペシャリストです。
        ユーザーの質問に対して、特に「さくらみこ」の最新の活動情報、配信、コラボ、
        SNS更新、イベント参加などについて正確な情報を収集することに重点を置いています。
        
        事実に基づく情報を提供し、不確かな情報は避けてください。必要に応じて検索ツールや
        YouTube検索ツールを使用して最新の情報を取得してください。現在時刻の情報が
        クエリに含まれている場合は、その時点での最新情報を提供するよう努めてください。
        """
        self.openai_agent.setup(researcher_prompt, self.common_tools)

        # Claude: アナライザー役割
        analyzer_prompt = """
        あなたはホロライブのVTuber「さくらみこ」に関する情報分析のスペシャリストです。
        収集された「さくらみこ」に関する情報を批判的に分析し、その信頼性と重要度を
        評価します。特に、配信やコンテンツのトレンド、ファンの反応、他のVTuberとの
        関係性などを多角的に分析してください。
        
        分析には必要に応じて検索ツールやYouTube検索ツールを活用し、情報の裏付けを
        取ることも重要です。現在時刻の情報が与えられた場合は、それを考慮して
        最新の状況を分析してください。
        """
        self.claude_agent.setup(analyzer_prompt, self.common_tools)

        # Gemini: クリエイター役割
        creator_prompt = """
        あなたはホロライブのVTuber「さくらみこ」に関する創造的な提案や
        エンターテイメント的な視点を提供するスペシャリストです。「さくらみこ」の
        最新情報に基づいて、ファンが楽しめるコンテンツ提案、今後の活動予測、
        おすすめの配信回やハイライトなどを提案してください。
        
        独創的かつ「さくらみこ」のキャラクター性に合った視点を提供することを
        心がけ、必要に応じて検索ツールやYouTube検索ツールを使用して
        情報を補完してください。現在時刻の情報が与えられた場合は、
        それを踏まえたタイムリーな提案を行ってください。
        """
        self.gemini_agent.setup(creator_prompt, self.common_tools)

    @tool
    def youtube_search(self, query: str) -> str:
        """
        クエリに関連するYouTubeビデオを検索します。

        Args:
            query: YouTube検索クエリ。

        Returns:
            YouTube検索結果をフォーマットした文字列。
        """
        # 実装はシングルエージェントからの移植
        import os
        import requests

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

    def run(
        self, 
        query: str,
        agents_to_use: Optional[List[AgentRole]] = None
    ) -> Dict[str, Any]:
        """
        指定されたクエリに対して複数のエージェントを実行し、結果を集約します。

        Args:
            query: ユーザーからのクエリ。
            agents_to_use: 使用するエージェントの役割リスト。指定しない場合はすべて使用。

        Returns:
            各エージェントの結果と集約結果を含む辞書。
        """
        results = {}
        
        # デフォルトではすべてのエージェントを使用
        if agents_to_use is None:
            agents_to_use = list(AgentRole)
            
        # 各エージェントを実行
        if AgentRole.RESEARCHER in agents_to_use:
            results["researcher"] = self.openai_agent.run(query)
            
        if AgentRole.ANALYZER in agents_to_use:
            results["analyzer"] = self.claude_agent.run(query)
            
        if AgentRole.CREATOR in agents_to_use:
            results["creator"] = self.gemini_agent.run(query)
            
        # 結果の集約
        aggregated_output = self._aggregate_results(results)
        results["aggregated"] = aggregated_output
        
        return results
    
    def _aggregate_results(self, results: Dict[str, Dict[str, Any]]) -> str:
        """
        各エージェントの結果を集約して統合された回答を生成します。

        Args:
            results: 各エージェントからの結果を含む辞書。

        Returns:
            集約された回答の文字列。
        """
        # 簡略化のため、各エージェントの出力を結合
        aggregated = "# マルチLLMエージェントからの集約結果\n\n"
        
        if "researcher" in results:
            aggregated += "## リサーチ結果（OpenAI）\n"
            aggregated += f"{results['researcher']['output']}\n\n"
            
        if "analyzer" in results:
            aggregated += "## 分析結果（Claude）\n"
            aggregated += f"{results['analyzer']['output']}\n\n"
            
        if "creator" in results:
            aggregated += "## 創造的提案（Gemini）\n"
            aggregated += f"{results['creator']['output']}\n\n"
            
        # 本来はここでメタエージェントが結果を分析し、より高度な集約を行うべき
        
        return aggregated


if __name__ == "__main__":
    # 使用例
    try:
        manager = MultiLLMAgentManager()
        result = manager.run("AIを活用した教育の未来について教えてください")
        print(result["aggregated"])
    except ValueError as e:
        print(f"エラー: {e}")
        print("必要なAPI環境変数を設定してから実行してください。")
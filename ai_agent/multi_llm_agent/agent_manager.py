from enum import Enum, auto
from typing import Any, Dict, List, Optional

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

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

        # メタエージェントの初期化 (GPT-4を使用)
        self.meta_agent = ChatOpenAI(model="gpt-4o", temperature=0.7)

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
        self, query: str, agents_to_use: Optional[List[AgentRole]] = None
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
        メタエージェントを使用して結果を分析し、高度な集約を行います。

        Args:
            results: 各エージェントからの結果を含む辞書。

        Returns:
            集約された回答の文字列。
        """
        # 各エージェントの結果を整理
        raw_results = {}

        if "researcher" in results and "output" in results["researcher"]:
            raw_results["researcher"] = results["researcher"]["output"]
        else:
            # 部分的な結果や中間出力の処理
            intermediate_results = ""
            if (
                "researcher" in results
                and "intermediate_steps" in results["researcher"]
            ):
                for step in results["researcher"]["intermediate_steps"]:
                    # ツール名と入力を取得
                    tool = step[0]
                    if hasattr(tool, "name"):
                        tool_name = tool.name
                    else:
                        tool_name = "unknown_tool"

                    tool_input = step[1]
                    tool_output = step[2]

                    # 中間ステップの情報を追加
                    intermediate_results += f"- {tool_name}：{tool_input}\n"
                    # 検索結果は長いため、一部のみ表示
                    if len(str(tool_output)) > 300:
                        tool_output = str(tool_output)[:300] + "...(省略)"
                    intermediate_results += f"  結果：{tool_output}\n\n"

            if intermediate_results:
                raw_results["researcher"] = (
                    f"収集された部分的な情報：\n{intermediate_results}"
                )
            else:
                raw_results["researcher"] = (
                    "反復制限または時間制限により処理が完了せず、十分な情報を収集できませんでした。"
                )

        if "analyzer" in results and "output" in results["analyzer"]:
            raw_results["analyzer"] = results["analyzer"]["output"]
        else:
            raw_results["analyzer"] = "分析結果が生成されませんでした。"

        if "creator" in results and "output" in results["creator"]:
            raw_results["creator"] = results["creator"]["output"]
        else:
            raw_results["creator"] = "創造的提案が生成されませんでした。"

        # メタエージェントによる高度な集約
        meta_prompt = f"""
        あなたはマルチLLMエージェントシステムにおけるメタエージェントです。
        3つの異なるLLM（OpenAI、Claude、Gemini）が異なる役割で同じクエリを処理した結果を受け取りました。
        これらの結果を分析し、整合性のある総合的な回答を生成してください。

        各エージェントの役割と結果は以下の通りです：

        1. リサーチャー（OpenAI GPT-4o-mini）:
        情報収集の専門家として、事実に基づく最新情報を提供しています。

        {raw_results["researcher"]}

        2. アナライザー（Claude）:
        情報分析の専門家として、収集された情報を批判的に分析し評価しています。

        {raw_results["analyzer"]}

        3. クリエイター（Gemini）:
        創造的提案の専門家として、独創的な視点やコンテンツを提供しています。

        {raw_results["creator"]}

        これらの情報を統合し、以下の点を考慮して総合的な回答を生成してください：
        
        1. 各エージェントの強みを活かした統合
        2. 情報の整合性チェックと矛盾の解消
        3. 重要な洞察や発見の強調
        4. 論理的で一貫性のある構成
        5. ユーザーにとって実用的な情報の優先
        
        回答はマークダウン形式で、適切な見出しと構造を持つように整形してください。
        また、反復は避け、簡潔かつ包括的な内容を心がけてください。
        """

        # メタエージェントによる集約の実行
        meta_response = self.meta_agent.invoke(
            [
                SystemMessage(
                    content="あなたはマルチエージェントシステムのメタエージェントです。複数のLLMからの出力を分析・集約し、高品質な統合回答を生成します。"
                ),
                HumanMessage(content=meta_prompt),
            ]
        )

        meta_analysis = meta_response.content

        # 生のエージェント結果とメタエージェントの分析を組み合わせた最終出力
        aggregated = "# マルチLLMエージェントからの集約結果\n\n"
        aggregated += meta_analysis

        # 元のエージェント出力をセクションとして追加（任意）
        aggregated += "\n\n## 各エージェントの詳細結果\n\n"

        aggregated += "### リサーチ結果（OpenAI）\n"
        aggregated += f"{raw_results['researcher']}\n\n"

        aggregated += "### 分析結果（Claude）\n"
        aggregated += f"{raw_results['analyzer']}\n\n"

        aggregated += "### 創造的提案（Gemini）\n"
        aggregated += f"{raw_results['creator']}\n\n"

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

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import BaseTool

from ai_agent.multi_llm_agent.base_agent import BaseAgent

load_dotenv()


class ClaudeAgent(BaseAgent):
    """
    Anthropic Claudeモデルを使用したエージェント実装。
    """

    def __init__(
        self, model_name: str = "claude-3-haiku-20240307", temperature: float = 0.7
    ):
        """
        ClaudeAgentを初期化します。

        Args:
            model_name: 使用するClaudeモデル。デフォルトはclaude-3-haiku-20240307。
            temperature: 生成の温度パラメータ。
        """
        super().__init__(model_name, temperature)
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY環境変数が設定されていません。")

        self.llm = ChatAnthropic(
            api_key=self.api_key,
            model_name=self.model_name,
            temperature=self.temperature,
        )
        self.agent_executor = None
        self.system_prompt = ""

    def setup(self, system_prompt: str, tools: Optional[List[BaseTool]] = None) -> None:
        """
        エージェントをセットアップします。

        Args:
            system_prompt: エージェントのシステムプロンプト。
            tools: エージェントに提供するツールのリスト。
        """
        if tools:
            self.tools = tools

        self.system_prompt = system_prompt

        # Claude用のカスタムエージェント作成

        # ツール説明の作成
        tools_str = "\n".join(
            [f"{tool.name}: {tool.description}" for tool in self.tools]
        )

        # 拡張したシステムプロンプト
        extended_system_prompt = f"""
{system_prompt}

あなたは以下のツールを使用してタスクを実行できます：

{tools_str}

ツールを使用するには、次の形式で応答してください：

Thought: タスクについて考えます
Action: 使用するツール名
Action Input: ツールの入力パラメータ
Observation: ツールからの出力結果

この過程を繰り返し、最終的な回答に到達したら：

Thought: これで十分な情報が集まりました
Final Answer: タスクへの最終回答

重要なルール:
1. 同じ検索クエリを2回以上実行しないでください
2. 十分な情報が集まったら、すぐに最終回答に進んでください
3. 検索結果は要約して活用してください
4. 最大3回のツール使用で結論を出してください

必ず上記の形式に従ってください。
"""

        # マニュアルエージェント作成
        def _run_agent(inputs: Dict[str, Any]) -> Dict[str, Any]:
            # 初期入力
            query = inputs["input"]

            # 会話履歴の初期化
            chat_history = [SystemMessage(content=extended_system_prompt)]
            chat_history.append(HumanMessage(content=query))

            # 使用したクエリを追跡
            used_queries = set()

            # エージェントのループ
            max_iterations = 3  # 最大反復回数を5回に制限
            for iteration in range(max_iterations):
                # LLMからの回答を取得
                ai_message = self.llm.invoke(chat_history)

                # AIの応答を解析
                response_text = ai_message.content

                # 「Final Answer:」を含む場合、最終回答とみなす
                if "Final Answer:" in response_text:
                    final_answer = response_text.split("Final Answer:")[1].strip()
                    return {"output": final_answer}

                # ツール使用パターンを解析
                try:
                    # "Action:" と "Action Input:" を抽出
                    action_match = (
                        response_text.split("Action:")[1].split("\n")[0].strip()
                    )
                    action_input_match = (
                        response_text.split("Action Input:")[1].split("\n")[0].strip()
                    )

                    # 同じクエリの繰り返しをチェック
                    if (
                        action_match.lower() == "duckduckgo_search"
                        and action_input_match in used_queries
                    ):
                        # 同じクエリを繰り返している場合、最終回答に促す
                        chat_history.append(AIMessage(content=response_text))
                        chat_history.append(
                            HumanMessage(
                                content=f"Observation: 同じクエリ '{action_input_match}' が既に使用されています。既に十分な情報が得られているため、最終回答に進んでください。"
                            )
                        )
                        continue

                    # 検索クエリを記録
                    if action_match.lower() == "duckduckgo_search":
                        used_queries.add(action_input_match)

                    # 該当するツールを検索
                    selected_tool = None
                    for tool in self.tools:
                        if tool.name.lower() == action_match.lower():
                            selected_tool = tool
                            break

                    if selected_tool:
                        # ツールを実行
                        observation = selected_tool.invoke(action_input_match)

                        # 会話履歴に追加
                        chat_history.append(AIMessage(content=response_text))

                        # 最後のイテレーションに近づいている場合、最終回答を促す
                        if iteration >= max_iterations - 2:
                            observation += "\n\n十分な情報が集まりました。これまでの情報を総合して最終回答をまとめてください。"

                        chat_history.append(
                            HumanMessage(content=f"Observation: {observation}")
                        )
                    else:
                        # ツールが見つからない場合
                        chat_history.append(AIMessage(content=response_text))
                        chat_history.append(
                            HumanMessage(
                                content=f"Observation: Error: ツール '{action_match}' は利用できません。既存の情報を使って最終回答を出してください。"
                            )
                        )
                except Exception as e:
                    # 解析エラーの場合
                    chat_history.append(AIMessage(content=response_text))
                    chat_history.append(
                        HumanMessage(
                            content=f"Observation: Error: {str(e)}。既存の情報を使って最終回答を出してください。"
                        )
                    )

            # 最大イテレーション数に達した場合、最後にもう一度チャンスを与える
            chat_history.append(
                HumanMessage(
                    content="最大反復回数に達しました。これまでに得られた情報を総合して、最終回答を提供してください。"
                )
            )

            # 最後の試み
            final_attempt = self.llm.invoke(chat_history)
            final_text = final_attempt.content

            # Final Answerがあれば抽出、なければそのまま
            if "Final Answer:" in final_text:
                final_answer = final_text.split("Final Answer:")[1].strip()
                return {"output": final_answer}
            else:
                return {"output": final_text}

        # LangChainのRunnableに変換
        runnable_agent = RunnablePassthrough.assign(output=_run_agent)

        # 実行エージェントの設定
        self.agent_executor = runnable_agent

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

        return self.agent_executor.invoke({"input": query})

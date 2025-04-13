"""
マルチLLMエージェントの使用例を示すスクリプト。
ホロライブVTuber「さくらみこ」の最新情報を取得します。
"""

import datetime
import os
from typing import Dict, List

from ai_agent.multi_llm_agent.agent_manager import AgentRole, MultiLLMAgentManager


def check_api_keys() -> Dict[str, bool]:
    """
    必要なAPI環境変数が設定されているかチェックします。

    Returns:
        各APIキーの設定状況を示す辞書。
    """
    keys = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY") is not None,
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY") is not None,
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY") is not None,
        "YOUTUBE_API_KEY": os.environ.get("YOUTUBE_API_KEY") is not None,
    }
    return keys


def run_example(agents_to_use: List[AgentRole] = None) -> None:
    """
    マルチLLMエージェントの実行例を示します。
    さくらみこの最新情報を取得します。

    Args:
        agents_to_use: 使用するエージェントの役割リスト。
    """
    # API環境変数のチェック
    api_keys = check_api_keys()
    missing_keys = [key for key, available in api_keys.items() if not available]

    if missing_keys:
        print(f"警告：以下のAPI環境変数が設定されていません: {', '.join(missing_keys)}")
        print("利用可能なすべてのエージェントが動作しない可能性があります。\n")

    try:
        # 現在時刻の取得
        current_time = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        # クエリ構築
        query = f"現在時刻は{current_time}です。さくらみこの最新活動情報は？"

        # マルチエージェントマネージャーの初期化
        manager = MultiLLMAgentManager()

        # クエリ実行
        print(f"クエリ: {query}\n")
        print("処理中...\n")
        result = manager.run(query, agents_to_use)

        # 結果表示
        print(result["aggregated"])

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")


if __name__ == "__main__":
    # すべてのエージェントを使う例
    run_example()

    # 特定のエージェントのみを使う例
    # run_example([AgentRole.RESEARCHER, AgentRole.CREATOR])

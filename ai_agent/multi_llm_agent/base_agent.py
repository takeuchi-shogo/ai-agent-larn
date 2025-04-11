from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool


class BaseAgent(ABC):
    """
    すべてのLLMエージェントの基底クラス。
    各LLMプロバイダー用のエージェントはこのクラスを継承します。
    """

    def __init__(self, model_name: str, temperature: float = 0.7):
        """
        BaseAgentを初期化します。

        Args:
            model_name: 使用するモデル名。
            temperature: 生成の温度パラメータ。
        """
        self.model_name = model_name
        self.temperature = temperature
        self.tools: List[BaseTool] = []

    @abstractmethod
    def setup(self, system_prompt: str, tools: Optional[List[BaseTool]] = None) -> None:
        """
        エージェントをセットアップします。

        Args:
            system_prompt: エージェントのシステムプロンプト。
            tools: エージェントに提供するツールのリスト。
        """
        pass

    @abstractmethod
    def run(self, query: str) -> Dict[str, Any]:
        """
        クエリに対してエージェントを実行します。

        Args:
            query: ユーザーからのクエリ。

        Returns:
            エージェントの応答を含む辞書。
        """
        pass
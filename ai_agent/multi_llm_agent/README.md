# マルチLLMエージェント

このディレクトリには、複数のLLM（OpenAI、Claude、Gemini）を使用したマルチエージェントの実装が含まれています。

## 概要

マルチLLMエージェントは以下のコンポーネントで構成されています：

- `agent_manager.py`: 複数のLLMエージェントを管理し、タスクの分配と結果の集約を行います
- `openai_agent.py`: OpenAIのモデルを使用したエージェントの実装
- `claude_agent.py`: Anthropicのモデルを使用したエージェントの実装
- `gemini_agent.py`: GoogleのGeminiモデルを使用したエージェントの実装
- `base_agent.py`: すべてのLLMエージェントの基底クラスを定義します

## アーキテクチャと処理フロー

マルチLLMエージェントシステムは以下のような役割分担とフローで動作します：

```mermaid
graph TD
    A[ユーザークエリ入力<br>「さくらみこの最新活動情報は？」] --> B[MultiLLMAgentManager<br>クエリの分配と最終結果の集約を担当]
    B --> C[OpenAI Agent<br>リサーチャー役割]
    B --> D[Claude Agent<br>アナライザー役割]
    B --> E[Gemini Agent<br>クリエイター役割]
    C --> F[情報収集結果]
    D --> G[分析結果]
    E --> H[創造的提案]
    F --> I[メタエージェント<br>GPT-4oを使用]
    G --> I
    H --> I
    I --> J[高度に統合された<br>最終結果]
    J --> K[詳細な各エージェント<br>結果を付加]
    K --> L[ユーザーに提示]
```

### シーケンス図

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant Manager as MultiLLMAgentManager
    participant OpenAI as OpenAI Agent<br>(リサーチャー)
    participant Claude as Claude Agent<br>(アナライザー)
    participant Gemini as Gemini Agent<br>(クリエイター)
    participant Meta as メタエージェント<br>(GPT-4o)
    
    User->>Manager: クエリ送信「さくらみこの最新活動情報は？」
    par 並行処理
        Manager->>OpenAI: クエリ転送
        OpenAI->>OpenAI: リサーチャーとして情報収集
        OpenAI-->>Manager: 情報収集結果を返す
    and
        Manager->>Claude: クエリ転送
        Claude->>Claude: アナライザーとして情報分析
        Claude-->>Manager: 分析結果を返す
    and
        Manager->>Gemini: クエリ転送
        Gemini->>Gemini: クリエイターとして創造的提案を作成
        Gemini-->>Manager: 創造的提案を返す
    end
    
    Manager->>Meta: 3つのエージェント結果を転送
    Meta->>Meta: 結果を統合分析・高度な集約を実行
    Meta-->>Manager: 統合された高品質な回答を返す
    Manager-->>User: 最終結果を提示
```

### 各LLMの役割分担

1. **OpenAI Agent (リサーチャー)** - 情報収集役
   - 使用モデル: `gpt-4o-mini`
   - 主な役割: さくらみこに関する事実情報の収集
   - ツール: Web検索、YouTube検索
   - 特徴: 正確な情報収集と最新情報の取得に特化

2. **Claude Agent (アナライザー)** - 情報分析役
   - 使用モデル: `claude-3-haiku-20240307`
   - 主な役割: 収集された情報の分析と評価
   - ツール: Web検索、YouTube検索
   - 特徴: 情報の信頼性評価、多角的な視点での分析

3. **Gemini Agent (クリエイター)** - 創造的提案役
   - 使用モデル: `gemini-pro`
   - 主な役割: 創造的なコンテンツやアイデアの提案
   - ツール: Web検索、YouTube検索
   - 特徴: 収集情報に基づく独創的な提案や表現

4. **メタエージェント (インテグレーター)** - 結果集約役
   - 使用モデル: `gpt-4o`
   - 主な役割: 3つのエージェント結果の分析と高度な統合
   - 特徴: 情報の整合性確認、矛盾の解消、重要ポイントの強調

### 処理フロー

1. ユーザーが「さくらみこの最新活動情報は？」と質問
2. `MultiLLMAgentManager`が各エージェントにクエリを分配
3. 各エージェントが処理を実行:
   - OpenAIエージェント: 最新の活動情報を検索・収集
   - Claudeエージェント: 収集情報の分析と重要度評価
   - Geminiエージェント: 活動情報に基づく創造的視点の提供
4. 各エージェントの結果をメタエージェント(GPT-4o)が分析・集約
   - 整合性チェック、矛盾の解消
   - 重要な洞察の強調
   - 論理的で一貫性のある構成の生成
5. 高度に統合された回答と詳細な各エージェント結果をユーザーに提示

## メタエージェントの統合プロセス

メタエージェントは反復処理を行わず、一度の処理で3つのエージェント結果を分析し高度な集約を行います：

1. 各エージェントの強みを活かした情報の統合
2. 情報の整合性チェックと矛盾している部分の解消
3. 重要な洞察や発見の強調
4. 論理的で一貫性のある構成の作成
5. ユーザーにとって実用的な情報の優先

## 使用方法

```python
from ai_agent.multi_llm_agent.agent_manager import MultiLLMAgentManager
import datetime

# 現在時刻の取得
current_time = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

# マルチエージェントマネージャーの初期化
manager = MultiLLMAgentManager()

# クエリの実行
result = manager.run(f"現在時刻は{current_time}です。さくらみこの最新活動情報は？")
print(result["aggregated"])
```

## 設定

以下の環境変数を設定する必要があります：

- `OPENAI_API_KEY`: OpenAIのAPIキー
- `ANTHROPIC_API_KEY`: AnthropicのAPIキー
- `GOOGLE_API_KEY`: GoogleのAPIキー（Gemini用）
- `YOUTUBE_API_KEY`: YouTube検索用のAPIキー

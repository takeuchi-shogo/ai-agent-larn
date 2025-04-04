# LangGraph 実装

このディレクトリには、LangGraphを使用した3つの異なるタイプのグラフ実装が含まれています。各実装は、異なる複雑さと目的を持っています。

## 1. シンプルグラフ (simple_graph.py)

最もシンプルな実装で、単一のノードから構成されるグラフです。

### 状態定義

```python
class SimpleState(TypedDict):
    question: str     # ユーザーからの質問
    response: str     # 生成された応答
```

### グラフ構造

```
[Entry Point] -> [generate_response] -> [Finish Point]
```

- **generate_response**: 質問を受け取り、LLMを使用して応答を生成

## 2. 決定グラフ (decision_graph.py)

ツールを使用した複雑な決定グラフです。計画立案、ツール選択、実行、結果合成を行います。

### 状態定義

```python
class DecisionState(TypedDict):
    question: str         # ユーザーからの質問
    thought: str          # 思考プロセス
    plan: List[str]       # 実行計画（ステップのリスト）
    current_step: int     # 現在のステップインデックス
    tools_output: List[str] # ツール実行の出力結果
    final_answer: str     # 最終的な回答
```

### グラフ構造

```
[Entry Point] -> [plan] -> [prepare_tool] --(条件分岐)--
                             |                |
                             v                v
                          [tool] <---------   [synthesize] -> [Finish Point]
                             |
                             |
                             +----------------+
```

- **plan**: 質問を分析し、思考プロセスと実行計画を生成
- **prepare_tool**: 次に使用するツールとその入力を決定
- **tool**: 実際にツールを実行（検索や計算など）
- **synthesize**: 集めた情報をもとに最終的な回答を生成

### 条件分岐

1. `prepare_tool`から`tool`への分岐: ツールが必要な場合
2. `prepare_tool`から`synthesize`への分岐:
   - すべての計画ステップが完了した場合
   - または、ツールが指定されなかった場合

## 3. チャットグラフ (chat_graph.py)

会話を処理するためのグラフで、メッセージのやり取りをモデル化しています。

### 状態定義
```python
class Message(TypedDict):
    role: str         # メッセージの送信者の役割（"user"または"assistant"）
    content: str      # メッセージの内容

class ChatState(TypedDict):
    messages: List[Message]          # 会話の履歴
    context: Optional[Dict[str, Any]] # 追加のコンテキスト情報
```

### グラフ構造
```
                 +--------+
                 |        |
[Entry Point] -> [generate_response] --(条件分岐)--> [END]
                 |        |
                 +--------+
```

- **generate_response**: 会話履歴を受け取り、次の応答を生成

### 条件分岐
- 最後のメッセージがアシスタントからの場合: 終了
- それ以外の場合: 継続して`generate_response`ノードに戻る

## 共通の特徴

すべてのグラフは以下の共通の特徴を持っています：

1. **LLMの統合**: OpenAI APIを使用したLLMの統合
2. **状態管理**: TypedDictによる型付き状態管理
3. **コンパイル**: グラフは実行前にコンパイルされ、最適化されます
4. **条件付きエッジ**: 状態に基づいた条件付きのフロー制御

## 使用例

これらのグラフは、`main.py`から以下のように呼び出せます：

```python
# シンプルグラフの例
graph = create_simple_graph()
result = graph.invoke({"question": "AIとヒトの協調について教えてください"})

# 決定グラフの例
graph = create_decision_graph()
result = graph.invoke({"question": "2025年の7月の最初の月曜日は何日ですか？"})

# チャットグラフの例
graph = create_chat_graph()
messages = [{"role": "user", "content": "AIの応用事例について教えてください"}]
result = graph.invoke({"messages": messages, "context": {}})
```

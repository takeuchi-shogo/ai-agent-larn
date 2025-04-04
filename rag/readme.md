# RAG実装とシンプルなLLMの比較

このディレクトリには、Retrieval Augmented Generation (RAG) を実装したコードとシンプルなLLMのコード例が含まれています。

## 主要なファイル

- `simple_llm.py`: RAGを実装していない通常のLLMによる質問応答の実装
- `qdrant_db.py`: Qdrantベクトルデータベースを使用したドキュメント管理
- `rag_chain.py`: RAGを使用した質問応答チェーンの実装
- `cli.py`: コマンドラインインターフェース
- `demo.py`: RAGとシンプルなLLMの比較デモ

## シンプルなLLMの制限

RAGを実装せずにLLMだけで質問に回答する場合、以下のような制限があります：

1. **知識の古さ**: モデルの学習データの切り取り日以降の情報が含まれない
2. **ハルシネーション**: 知らない情報を作り上げる可能性がある
3. **ソースの欠如**: 情報源を提示できない

## RAGの実装

このプロジェクトでは、以下のRAG実装が含まれています：

1. **ドキュメント処理**: テキストファイルを読み込み、適切なチャンクに分割
2. **ベクトル化**: OpenAIの埋め込みモデルを使用してテキストをベクトル化
3. **ベクトルデータベース**: Qdrantを使用してベクトルとテキストを保存
4. **検索**: ユーザーの質問に類似したテキストチャンクを検索
5. **応答生成**: 検索結果をプロンプトに組み込み、LLMで回答を生成

## RAGとLLMの比較

RAG実装では、以下のような改善が得られます：

1. **最新情報へのアクセス**: 外部データソースから最新の情報を取得できる
2. **事実に基づく回答**: 実際のドキュメントに基づいた回答が可能
3. **さくらみこに関する専門的な情報**: 公式情報に基づく正確な回答が可能
4. **ソースの透明性**: 情報の出所を明示できる
5. **知識のギャップの低減**: モデルの学習されていない情報を補完できる

## 使用方法

### 1. ベクトルデータベースの準備

Dockerを使用してQdrantを起動します：

```bash
docker compose up -d qdrant
```

### 2. CLIを使ってRAGでの質問応答

```bash
# ベクトルデータベースを初期化して質問に回答
python -m rag.cli --init --query "さくらみこについて教えてください"

# 既存のベクトルデータベースを使用（インタラクティブモード）
python -m rag.cli
```

### 3. RAGとLLMの比較デモ

```bash
python -m rag.demo
```

### 4. Pythonからの利用例

```python
from rag.qdrant_db import initialize_vectordb
from rag.rag_chain import ask_about_sakura_miko_with_rag

# ベクトルデータベースの初期化（初回のみ）
file_path = "data/hololive/sakura-miko.txt"
vectorstore = initialize_vectordb(file_path)

# 質問応答
question = "さくらみこの配信活動について教えてください"
response = ask_about_sakura_miko_with_rag(question, vectorstore)
print(response)
```

## 技術スタック

- **LangChain**: RAGパイプラインの構築
- **OpenAI API**: 埋め込みとLLM
- **Qdrant**: ベクトルデータベース
- **Docker**: Qdrantのコンテナ化
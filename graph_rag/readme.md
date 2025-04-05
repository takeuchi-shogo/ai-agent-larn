# GraphRAG - グラフデータベースを使用したRAG実装

GraphRAGは、Neo4jグラフデータベースとQdrantベクトルデータベースを組み合わせた高度なRAG（Retrieval Augmented Generation）システムです。テキストデータから抽出した構造化情報をグラフデータベースに格納し、知識グラフとベクトル検索を組み合わせて質問応答を行います。

## 概要

GraphRAGは以下の特徴を持ちます：

1. **知識グラフの構築**: テキストからエンティティ（人物、組織、イベントなど）とその関係を抽出し、Neo4jに格納
2. **セマンティック検索**: Qdrantベクトルデータベースを使用した意味的類似性検索
3. **ハイブリッド検索**: グラフデータベースとベクトルデータベースの両方から情報を検索
4. **コンテキスト拡張**: 関連エンティティを通じて情報の文脈を拡張

## アーキテクチャ

![GraphRAGアーキテクチャ](https://mermaid.ink/img/pako:eNqFkk9LAzEQxb_KMicFtVBdL4KH9uBJULyJlGWabGuwSUgmQpf97k6y3T-Cggkhk_fem8xLTkIZh6IUkXFWo6MrVFrz5NCYcXewGg19a1IaA4HxYnrATMYHw8nQZZTxvDlJL2YDWRvXCiX78i5sWN6dP17Ozh5mi-VitZw_387Sc8W8h0eDR8pKBZPQqKzibRdgOlBHhXXnrEcnFQBucvjJYdwEmOvz8_WfDK53-jZDoyytDQr2qr-O_g5GCKd3S-UQe-TJJHPtGdVMGmBOK5ANQq0MZI9WGnTO1Mx-42jQvFvrm8fXcNIxR8TQ_rEMpzT0-HXYaqf-e5jtrJeibKGFoGqpSDXg2dVGqSbsJoZwvhNiobQXcvLWgTQyQQsflJYicb6DDiZiDC1v-xKxxqRVYbcJ1S8x1rA4?type=png)

## インストール

### 前提条件

- Docker
- Python 3.13以上
- OpenAI API キー

### セットアップ

1. Neo4jとQdrantのDockerコンテナを起動します：

```bash
docker-compose up -d neo4j qdrant
```

2. 依存関係をインストールします：

```bash
uv pip install -e .
```

3. `.env`ファイルを作成し、APIキーを設定します：

```
OPENAI_API_KEY=your_api_key_here
```

## 使用方法

### テキストデータのロード

```python
from graph_rag.rag_graph import initialize_graph_rag

# GraphRAGの初期化とデータのロード
graph_rag = initialize_graph_rag(
    file_path="data/hololive/sakura-miko.txt",
    entity_type="VTuber",
    entity_id="sakura-miko"
)
```

### 質問応答

```python
# 質問の処理
question = "さくらみこの初のソロライブについて教えてください"
response = graph_rag.ask(question)
print(response)
```

### コマンドラインインターフェース

CLIツールも利用できます：

```bash
# データのロード
python -m graph_rag.cli load --file data/hololive/sakura-miko.txt --entity-type VTuber --entity-id sakura-miko

# 質問の処理
python -m graph_rag.cli ask --question "さくらみこの初のソロライブについて教えてください" --entity-id sakura-miko --entity-type VTuber
```

## デモの実行

デモを実行するには：

```bash
python -m graph_rag.main
```

## 仕組み

1. **テキスト処理**: テキストをチャンクに分割し、ベクトル化
2. **エンティティ抽出**: LLMを使用してエンティティと関係を抽出
3. **グラフ構築**: 抽出された情報をNeo4jグラフデータベースに格納
4. **ハイブリッド検索**: 
   - ベクトル検索: セマンティックな類似性に基づいて関連チャンクを検索
   - グラフ検索: エンティティと関係に基づいて構造化された情報を検索
5. **コンテキスト拡張**: グラフデータベースの関係を使用して情報の文脈を拡張
6. **生成**: 検索結果を使用してLLMが回答を生成

## 今後の展望

- 複数のデータソースの統合
- マルチモーダルデータのサポート
- より高度な推論機能
- 対話的なチャットインターフェース

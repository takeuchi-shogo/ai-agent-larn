"""
RAGを用いた質問応答チェーンの実装
"""

import datetime
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from rag.qdrant_db import initialize_vectordb

# 環境変数の読み込み
load_dotenv()

# APIキーの存在確認
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables")


def get_current_date() -> str:
    """現在の日付を取得する関数

    Returns:
        str: YYYY年MM月DD日 形式の日付文字列
    """
    today = datetime.datetime.now()
    return today.strftime("%Y年%m月%d日")


def format_docs(docs: List[Document]) -> str:
    """ドキュメントをフォーマットする

    Args:
        docs (List[Document]): ドキュメントのリスト

    Returns:
        str: フォーマットされたドキュメント文字列
    """
    return "\n\n".join(doc.page_content for doc in docs)


def create_rag_chain(
    vectorstore,
    model_name: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    k: int = 5,
):
    """RAGチェーンを作成する

    Args:
        vectorstore: 使用するベクトルストア
        model_name (str, optional): 使用するモデル名. デフォルトは"gpt-3.5-turbo"
        temperature (float, optional): 生成の温度. デフォルトは0.7
        k (int, optional): 検索する類似ドキュメントの数. デフォルトは5

    Returns:
        Chain: 実行可能なRAGチェーン
    """
    # LLMの初期化
    llm = ChatOpenAI(model_name=model_name, temperature=temperature)

    # 検索コンポーネントの設定
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})

    # プロンプトテンプレートの定義
    template = """あなたはさくらみこについて詳しく答えるアシスタントです。

今日の日付は{current_date}です。

以下の情報源を使用して質問に最善を尽くして答えてください。

情報源:
{context}

質問: {question}

回答に情報源から引用した部分があれば「(情報源より)」と明記してください。
情報源にない情報については「情報源にはこの情報がありません」と正直に伝えてください。
回答は日本語で簡潔に、かつ十分な情報量を含めるようにしてください。
"""

    # プロンプトの作成
    prompt = ChatPromptTemplate.from_template(template)

    # 出力パーサー
    output_parser = StrOutputParser()

    # RAGチェーンの構築
    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
            "current_date": lambda _: get_current_date(),
        }
        | prompt
        | llm
        | output_parser
    )

    return rag_chain


def ask_about_sakura_miko_with_rag(
    question: str, vectorstore=None, file_path: Optional[str] = None
) -> str:
    """RAGを使ってさくらみこについての質問に回答する

    Args:
        question (str): 質問文
        vectorstore: 既存のベクトルストア（Noneの場合は作成される）
        file_path (Optional[str], optional): データファイルのパス（ベクトルストアがNoneの場合に使用）

    Returns:
        str: 質問への回答
    """
    # ベクトルストアが提供されていない場合は作成
    if vectorstore is None:
        if file_path is None:
            file_path = "/Users/takeuchishougo/dev-app/ai/ai-agent-larn/data/hololive/sakura-miko.txt"

        # ベクトルデータベースを初期化
        vectorstore = initialize_vectordb(file_path)

    # RAGチェーンの作成
    chain = create_rag_chain(vectorstore)

    # 質問の処理
    response = chain.invoke(question)

    return response


def compare_llm_and_rag(
    question: str,
    file_path: str = "/Users/takeuchishougo/dev-app/ai/ai-agent-larn/data/hololive/sakura-miko.txt",
) -> Dict[str, str]:
    """通常のLLMとRAGの回答を比較する

    Args:
        question (str): 質問
        file_path (str, optional): データファイルのパス

    Returns:
        Dict[str, str]: 比較結果の辞書
    """
    from rag.simple_llm import create_simple_llm

    # 通常のLLM
    llm_chain = create_simple_llm()
    llm_response = llm_chain.invoke({"question": question})

    # RAG
    vectorstore = initialize_vectordb(file_path)
    rag_response = ask_about_sakura_miko_with_rag(question, vectorstore)

    return {
        "question": question,
        "llm_response": llm_response,
        "rag_response": rag_response,
    }


if __name__ == "__main__":
    # データファイルのパス
    file_path = (
        "/Users/takeuchishougo/dev-app/ai/ai-agent-larn/data/hololive/sakura-miko.txt"
    )

    # RAGの初期化とテスト
    vectorstore = initialize_vectordb(file_path)

    # テスト質問
    question = "さくらみこの配信活動について教えてください"
    response = ask_about_sakura_miko_with_rag(question, vectorstore)
    print(response)

    # 通常のLLMとRAGの比較
    comparison = compare_llm_and_rag(
        "さくらみこの初のソロライブについて教えてください", file_path
    )
    print("\n--- 通常のLLM ---\n")
    print(comparison["llm_response"])
    print("\n--- RAG ---\n")
    print(comparison["rag_response"])

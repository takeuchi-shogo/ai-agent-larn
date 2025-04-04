import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# 環境変数の読み込みを確実に行う
load_dotenv(override=True)

# APIキーの存在確認
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables")


def create_simple_chain(model_name="gpt-4o-mini-2024-07-18", temperature=0.7):
    """シンプルなLangChainチェーンを作成する

    Args:
        model_name (str, optional): 使用するモデル名. デフォルトは"gpt-4o-mini-2024-07-18".
        temperature (float, optional): 生成の温度. デフォルトは0.7.

    Returns:
        Chain: 実行可能なLangChainチェーン
    """

    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # プロンプトテンプレートの定義
    prompt = ChatPromptTemplate.from_template(
        "あなたは優秀なAIアシスタントです。次の質問に簡潔に答えてください: {question}"
    )

    # LLMモデルの定義
    model = ChatOpenAI(model_name=model_name, temperature=temperature)

    # 出力パーサー
    output_parser = StrOutputParser()

    # チェーンの構築
    chain = prompt | model | output_parser

    return chain


def create_rag_chain(retriever, model_name="gpt-3.5-turbo", temperature=0.7):
    """RAG (Retrieval Augmented Generation) チェーンを作成する

    Args:
        retriever: 文書検索用のretriever
        model_name (str, optional): 使用するモデル名. デフォルトは"gpt-3.5-turbo".
        temperature (float, optional): 生成の温度. デフォルトは0.7.

    Returns:
        Chain: 実行可能なRAGチェーン
    """
    # RAG用プロンプトテンプレート
    prompt = ChatPromptTemplate.from_template(
        """以下のコンテキスト情報が与えられています:
        
        {context}
        
        この情報を使って、次の質問に簡潔に答えてください: {question}
        
        もし回答がコンテキストにない場合は、「情報が不足しています」と答えてください。"""
    )

    # LLMモデルの定義
    model = ChatOpenAI(model_name=model_name, temperature=temperature)

    # 出力パーサー
    output_parser = StrOutputParser()

    # RAGチェーンの構築
    chain = (
        {
            "context": lambda x: retriever.get_relevant_documents(x["question"]),
            "question": lambda x: x["question"],
        }
        | prompt
        | model
        | output_parser
    )

    return chain

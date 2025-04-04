import datetime
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

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


def create_simple_llm(model_name="gpt-3.5-turbo", temperature=0.7):
    """シンプルなLLM呼び出しのチェーンを作成する

    Args:
        model_name (str, optional): 使用するモデル名. デフォルトは"gpt-3.5-turbo"
        temperature (float, optional): 生成の温度. デフォルトは0.7

    Returns:
        Chain: 実行可能なチェーン
    """
    # 実行時に現在の日付を取得するように設定
    llm = ChatOpenAI(model_name=model_name, temperature=temperature)

    # プロンプトテンプレートの定義
    prompt = ChatPromptTemplate.from_template(
        """あなたは最新の情報を提供するアシスタントです。

今日の日付は{current_date}です。

あなたの知識は学習時のデータが切り取られた時点までのもので、それ以降の情報は含みません。その点を正直に伝えてください。

以下の質問に答えてください：

{question}

回答には以下の形式で情報の制限を明示してください：

注意: 私の知識は学習データの最終更新日までの情報に限られています。それ以降の最新の動向には対応できない可能性があります。
"""
    )

    # 出力パーサー
    output_parser = StrOutputParser()

    # チェーンの構築
    chain = (
        (lambda x: {"question": x["question"], "current_date": get_current_date()})
        | prompt
        | llm
        | output_parser
    )

    return chain


def ask_about_sakura_miko():
    """さくらみこについての質問を処理する関数

    Returns:
        str: 質問に対する回答
    """
    # LLMチェーンの作成
    chain = create_simple_llm()

    # 質問の作成
    question = "さくらみこについて最近の動向を日付を添えて教えてください"

    # 質問の処理
    response = chain.invoke({"question": question})

    return response


def compare_with_rag():
    """単純なLLMとRAGの違いを説明する関数

    Returns:
        str: 違いの説明
    """
    explanation = """
# 単純なLLMとRAGの違い

## 単純なLLMの限界

このコードでは、LLMが学習したデータの時点までの知識に基づいて回答を生成しています。そのため、以下の問題があります：

1. 知識の古さ: モデルの学習データの切り取り日以降の情報が含まれない
2. ハルシネーション: 知らない情報を作り上げる可能性がある
3. ソースの欠如: 情報源を提示できない

## RAGを実装した場合の利点

このコードにRAGを実装すれば、以下のような利点が得られます：

1. 最新情報へのアクセス: 外部データソースから最新の情報を取得できる
2. 事実に基づく回答: 実際のドキュメントに基づいた回答が可能
3. さくらみこに関する専門的な情報: Youtube動画、ツイート、公式発表などの最新データを組み込める
4. ソースの透明性: 情報の出所を明示できる
5. 知識のギャップの低減: モデルの学習されていない情報を補完できる
"""

    return explanation


# コードを直接実行した場合の処理
if __name__ == "__main__":
    result = ask_about_sakura_miko()
    print(result)
    print("\n" + "-" * 50 + "\n")
    print(compare_with_rag())

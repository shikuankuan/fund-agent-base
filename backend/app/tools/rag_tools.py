"""RAG 工具：基于知识库回答问题"""

from typing import Optional
from langchain_core.tools import tool

from app.rag.rag_chain import load_rag_chain


@tool
def rag_query(query: str) -> str:
    """基于基金行业知识库回答问题。

    当用户询问基金行业相关知识、法规、术语解释等问题时，
    使用此工具从知识库中检索相关信息并生成回答。

    Args:
        query: 用户问题

    Returns:
        基于知识库的回答
    """
    # 加载 RAG Chain
    rag_chain = load_rag_chain()

    if rag_chain is None:
        return "❌ 知识库尚未初始化，请先运行 python -m app.rag.vector_store 初始化知识库。"

    try:
        # 调用 RAG Chain
        answer = rag_chain.invoke(query)

        return f"📚 基于知识库的回答：\n\n{answer}"

    except Exception as e:
        return f"❌ RAG 查询失败: {str(e)}"


# 测试代码
if __name__ == "__main__":
    print("测试 RAG 工具...")

    # 测试问题
    test_questions = ["什么是基金？", "基金有哪些风险？", "投资者适当性怎么分类？"]

    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"问题: {question}")
        print(f"{'='*60}")

        answer = rag_query(question)
        print(answer)

"""RAG Chain：检索 + 生成"""

from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import Chroma

from app.rag.embedding import get_embedding_model
from app.rag.vector_store import load_vector_store
from app.config import settings
from langchain_core.prompts import ChatPromptTemplate

# RAG Prompt 模板
RAG_PROMPT_TEMPLATE = """你是基金行业的专业助手。

根据以下参考文档回答问题。如果参考文档中没有相关信息，请明确说明"根据现有资料无法回答"，不要编造答案。

参考文档：
{context}

用户问题：{question}

要求：
1. 基于参考文档回答，不要编造
2. 如果文档中没有相关信息，明确说明
3. 回答要专业、准确、简洁
4. 可以引用文档中的具体内容
5. 使用中文回答

回答："""


def create_rag_chain(vector_store: Chroma, llm=None, top_k: int = 3):
    """创建 RAG Chain

    Args:
    vector_store: 向量数据库实例
    llm: 语言模型（默认使用 Qwen3）
    top_k: 检索 Top-K 个文档

    Returns:
    RAG Chain 实例
    """
    # 如果没有提供 LLM，使用默认的 Qwen3
    if llm is None:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            temperature=0.7,
        )

    # 创建检索器
    retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": top_k}
    )

    # 创建 Prompt 模板 (使用 ChatPromptTemplate.from_messages)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RAG_PROMPT_TEMPLATE),
            ("human", "{question}"),
        ]
    )

    # 创建 RAG Chain (使用新版函数式链式调用)
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    from langchain.schema import Document as LangChainDocument

    # 定义文档格式化函数
    def format_docs(docs: List[LangChainDocument]) -> str:
        return "\n\n".join([doc.page_content for doc in docs])

    # 构建链式调用
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print(f"✅ RAG Chain 创建成功！")
    print(f" - 检索 Top-K: {top_k}")
    print(f" - LLM: {llm.model_name if hasattr(llm, 'model_name') else 'Unknown'}")

    return rag_chain


def load_rag_chain(
    persist_directory: str = "./data/chroma_db",
    collection_name: str = "fund_knowledge_base",
    llm=None,
    top_k: int = 3,
):
    """加载向量数据库并创建 RAG Chain

    Args:
    persist_directory: 向量数据库持久化路径
    collection_name: 集合名称
    llm: 语言模型
    top_k: 检索 Top-K 个文档

    Returns:
    RAG Chain 实例，如果向量数据库不存在返回 None
    """
    # 加载 Embedding 模型
    embeddings = get_embedding_model()

    # 加载向量数据库
    vector_store = load_vector_store(
        persist_directory=persist_directory,
        embeddings=embeddings,
        collection_name=collection_name,
    )

    if vector_store is None:
        return None

    # 创建 RAG Chain
    rag_chain = create_rag_chain(vector_store=vector_store, llm=llm, top_k=top_k)

    return rag_chain


def test_rag_chain(rag_chain, test_questions: List[str]) -> None:
    """测试 RAG Chain

    Args:
    rag_chain: RAG Chain 实例
    test_questions: 测试问题列表
    """
    print(f"\n🧪 开始测试 RAG Chain...")

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {question}")
        print(f"{'='*60}")

        try:
            result = rag_chain.invoke(question)
            print(f"回答：\n{result}")
        except Exception as e:
            print(f"❌ 错误：{e}")

    print(f"\n✅ 测试完成！")


# 测试代码
if __name__ == "__main__":

    print("1. 加载向量数据库...")
    rag_chain = load_rag_chain()

    if rag_chain is None:
        print("❌ 向量数据库不存在，请先运行 python -m app.rag.vector_store")
        exit(1)

    print("\n2. 测试 RAG Chain...")
    test_questions = [
        "什么是基金？",
        "基金有哪些分类？",
        "基金的风险等级有哪些？",
        "投资者适当性是什么？",
    ]

    test_rag_chain(rag_chain, test_questions)

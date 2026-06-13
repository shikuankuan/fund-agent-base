"""向量存储：使用 ChromaDB"""

import os
from typing import List, Optional
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# 向量数据库持久化路径
PERSIST_DIRECTORY = "./data/chroma_db"


def create_vector_store(
    documents: List[Document],
    embeddings,
    persist_directory: str = PERSIST_DIRECTORY,
    collection_name: str = "fund_knowledge_base",
) -> Chroma:
    """创建向量存储

    Args:
        documents: Document 列表
        embeddings: Embedding 模型
        persist_directory: 持久化路径
        collection_name: 集合名称

    Returns:
        Chroma 向量存储实例
    """
    # 创建持久化目录
    os.makedirs(persist_directory, exist_ok=True)

    # 创建向量存储
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name=collection_name,
    )

    print(f"✅ 向量数据库创建成功！")
    print(f" - 文档数: {len(documents)}")
    print(f" - 存储路径: {persist_directory}")
    print(f" - 集合名称: {collection_name}")

    return vector_store


def load_vector_store(
    persist_directory: str = PERSIST_DIRECTORY,
    embeddings=None,
    collection_name: str = "fund_knowledge_base",
) -> Optional[Chroma]:
    """加载向量存储

    Args:
        persist_directory: 持久化路径
        embeddings: Embedding 模型
        collection_name: 集合名称

    Returns:
        Chroma 向量存储实例，如果不存在返回 None
    """
    if not os.path.exists(persist_directory):
        print(f"❌ 向量数据库不存在: {persist_directory}")
        return None

    # 加载向量存储
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name=collection_name,
    )

    # 获取文档数
    count = vector_store._collection.count()
    print(f"✅ 向量数据库加载成功！")
    print(f" - 文档数: {count}")
    print(f" - 存储路径: {persist_directory}")

    return vector_store


def add_documents_to_vector_store(
    vector_store: Chroma, documents: List[Document]
) -> None:
    """向已有向量存储添加文档

    Args:
        vector_store: Chroma 向量存储实例
        documents: 要添加的 Document 列表
    """
    vector_store.add_documents(documents)
    print(f"✅ 添加了 {len(documents)} 个文档到向量数据库")


# 测试代码
if __name__ == "__main__":
    # 避免在测试时无限递归导入
    import sys
    import os

    # 将项目根目录添加到 Python 路径
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from app.rag.document_loader import load_documents_from_directory
    from app.rag.text_splitter import split_documents
    from app.rag.embedding import get_embedding_model

    base_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(base_dir, "../docs")  # 自动解析路径
    # 加载并分割文档
    print("1. 加载文档...")
    docs = load_documents_from_directory(doc_path)
    print(f" 文档数: {len(docs)}")

    print("\n2. 分割文档...")
    chunks = split_documents(docs, chunk_size=200, chunk_overlap=30)
    print(f" 块数: {len(chunks)}")

    print("\n3. 获取 Embedding 模型...")
    embeddings = get_embedding_model()

    print("\n4. 创建向量存储...")
    vector_store = create_vector_store(chunks, embeddings)

    print("\n5. 验证向量存储（检索测试）...")
    result = vector_store.similarity_search("什么是基金？", k=2)
    print(f" 检索到 {len(result)} 个相关文档")
    for i, doc in enumerate(result):
        print(f" [{i+1}] {doc.page_content[:80]}...")

"""文本分块器：使用 RecursiveCharacterTextSplitter"""

from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def split_documents(
    documents: List[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: List[str] = None,
) -> List[Document]:
    """将文档分割成小块

    Args:
    documents: Document 列表
    chunk_size: 每个块的最大字符数
    chunk_overlap: 块之间的重叠字符数
    separators: 分隔符列表（按优先级排序）

    Returns:
    分割后的 Document 列表
    """
    if separators is None:
        # 默认分隔符：按优先级排序（适合中文）
        separators = [
            "\n\n",  # 段落分隔
            "\n",  # 换行符
            "。",  # 中文句号
            "！",  # 中文感叹号
            "？",  # 中文问号
            " ",  # 空格
            "",  # 字符级作为最后手段
        ]

    # 创建分块器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,  # 使用字符数作为长度函数
    )

    # 分割文档
    chunks = text_splitter.split_documents(documents)

    return chunks


def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """将文本分割成小块（不包含 metadata）

    Args:
    text: 要分割的文本
    chunk_size: 每个块的最大字符数
    chunk_overlap: 块之间的重叠字符数

    Returns:
    分割后的文本列表
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    chunks = text_splitter.split_text(text)

    return chunks


# 测试代码
if __name__ == "__main__":
    from document_loader import load_documents_from_directory
    import os

    base_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(base_dir, "../docs")  # 自动解析路径
    # 加载文档
    docs = load_documents_from_directory(doc_path)
    print(f"原始文档数: {len(docs)}")

    # 分割文档
    chunks = split_documents(docs, chunk_size=200, chunk_overlap=30)
    print(f"分割后块数: {len(chunks)}")

    # 打印前 3 个块
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- 块 {i+1} ---")
        print(f"内容: {chunk.page_content[:100]}...")
        print(f"来源: {chunk.metadata.get('source', 'unknown')}")

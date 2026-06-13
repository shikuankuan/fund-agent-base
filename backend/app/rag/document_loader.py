"""文档加载器：支持 PDF 和 Markdown"""

from typing import List
from langchain_community.document_loaders import PDFPlumberLoader, TextLoader
from langchain_core.documents import Document


def load_pdf_documents(pdf_path: str) -> List[Document]:
    """加载 PDF 文档

    Args:
    pdf_path: PDF 文件路径

    Returns:
    Document 列表
    """
    loader = PDFPlumberLoader(pdf_path)
    documents = loader.load()
    return documents


def load_markdown_documents(md_path: str) -> List[Document]:
    """加载 Markdown 文档

    Args:
    md_path: Markdown 文件路径

    Returns:
    Document 列表
    """
    loader = TextLoader(md_path, encoding="utf-8")
    documents = loader.load()
    return documents


def load_documents_from_directory(directory: str) -> List[Document]:
    """从目录加载所有文档

    Args:
    directory: 目录路径
    extensions: 要加载的文件扩展名列表

    Returns:
    Document 列表
    """
    from langchain_community.document_loaders import DirectoryLoader

    loader = DirectoryLoader(
        directory,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()
    return documents


# 测试代码
if __name__ == "__main__":
    import os

    base_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(base_dir, "../docs")  # 自动解析路径
    docs = load_documents_from_directory(doc_path)
    # 示例：从 docs 目录加载所有文档
    print(f"加载了 {len(docs)} 个文档")

    for doc in docs[:3]:
        print(f"\n--- 文档: {doc.metadata.get('source', 'unknown')} ---")
        print(f"内容（前200字）: {doc.page_content[:200]}...")

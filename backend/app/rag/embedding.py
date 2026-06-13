import os

# 当前脚本目录
cur_dir = os.path.dirname(os.path.abspath(__file__))
# 项目统一模型缓存目录
MODEL_CACHE = os.path.abspath(os.path.join(cur_dir, "../../model_cache/hf_cache"))
os.makedirs(MODEL_CACHE, exist_ok=True)

# 1. transformers/huggingface_hub 全局缓存
os.environ["HF_HOME"] = MODEL_CACHE
# 2. 强制国内镜像，解决网络校验失败重复下载
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# 3. sentence-transformers 专属缓存（根治 ST 不走 HF_HOME）
os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.path.join(MODEL_CACHE, "st_cache")
os.makedirs(os.environ["SENTENCE_TRANSFORMERS_HOME"], exist_ok=True)

# 环境变量必须写完再导入包！顺序不能调换！
from langchain_huggingface import HuggingFaceEmbeddings


def get_embedding_model():
    """获取 BAAI/bge-small-zh-v1.5 嵌入模型

    模型缓存路径:
    - SentenceTransformers: {MODEL_CACHE}/st_cache
    - Transformers/HF: {MODEL_CACHE}

    Returns:
        HuggingFaceEmbeddings: 初始化好的嵌入模型实例
    """
    model_name = "BAAI/bge-small-zh-v1.5"

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        # 缓存路径通过环境变量 SENTENCE_TRANSFORMERS_HOME / HF_HOME 控制
        model_kwargs={
            "trust_remote_code": True,
            # 关键：只从本地缓存读取，不联网下载
            "local_files_only": False,
        },
        encode_kwargs={"normalize_embeddings": True},
    )
    return embeddings

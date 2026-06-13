"""
测试LLM连通性
"""

import asyncio
from langchain_openai import ChatOpenAI
from app.config import settings


async def test_llm():
    """测试LLM连接"""
    print("正在测试LLM连通性...")
    print(f"模型: {settings.OPENAI_MODEL}")
    print(f"Base URL: {settings.OPENAI_BASE_URL}")

    # 创建LLM实例
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=0.7,
    )

    # 发送测试消息
    try:
        response = await llm.ainvoke("请用一句话介绍你自己")
        print("\n✅ LLM连接成功！")
        print(f"回复: {response.content}")
    except Exception as e:
        print(f"\n❌ LLM连接失败: {e}")
        print("请检查：")
        print("1. OPENAI_API_KEY 是否正确")
        print("2. 网络是否畅通（是否需要代理）")
        print("3. OPENAI_BASE_URL 是否正确")


if __name__ == "__main__":
    asyncio.run(test_llm())

# backend/test_qwen3.py
import sys, os

from backend.app.prompts.fund_prompts import FUND_ASSISTANT_PROMPT

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from app.config import settings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def test_qwen3():
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=0.7,
    )
    system_prompt = FUND_ASSISTANT_PROMPT
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="那混合型基金呢？请详细解释。"),
    ]

    print("思考中...")
    response = llm.invoke(messages)
    print(f"\n回答：\n{response.content}")
    print("\n✅ System Prompt 测试成功！")


if __name__ == "__main__":
    test_qwen3()

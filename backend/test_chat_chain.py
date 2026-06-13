# backend/test_chat_chain.py
import sys, os

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
from backend.app.prompts.fund_prompts import FUND_ASSISTANT_PROMPT
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory


def test_chat_chain():
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=0.7,
    )

    # ChatPromptTemplate 对话模板
    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system_prompt}"), ("human", "{question}")]
    )

    # Chain
    chain = prompt | llm | StrOutputParser()

    # 消息历史存储
    chat_history = InMemoryChatMessageHistory()

    # 带历史管理的chain
    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: chat_history,
        input_messages_key="question",
        history_messages_key="history",
    )

    system_prompt = FUND_ASSISTANT_PROMPT

    r1 = chain_with_history.invoke(
        {"system_prompt": system_prompt, "question": "什么是偏股混合型基金？"},
        config={"configurable": {"session_id": "user_123"}},
    )
    print(f"第1轮：{r1[:50]}...\n")

    # 第 2 轮（能记住第 1 轮）
    r2 = chain_with_history.invoke(
        {"system_prompt": system_prompt, "question": "它和股票型基金有什么区别？"},
        config={"configurable": {"session_id": "user_123"}},
    )
    print(f"第2轮：{r2[:100]}...")
    print("\n✅ 对话历史测试成功！")


if __name__ == "__main__":
    test_chat_chain()

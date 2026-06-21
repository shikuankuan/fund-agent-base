"""Agent 状态图构建"""

from langgraph.graph import StateGraph, END, START
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.agent.state import AgentState
from app.agent.nodes import (
    intent_recognizer,
    tool_selector,
    data_fetcher,
    analyzer,
    compliance_checker,
    response_generator,
)
from app.agent.router import (
    route_after_intent,
    route_by_intent,
    should_check_compliance,
    has_fund_code,
)

fund_agent_graph = None  # 启动后才赋值


async def init_graph():

    global fund_agent_graph
    # 创建checkpointer
    conn = aiosqlite.connect(".langgraph.db")
    checkpointer = AsyncSqliteSaver(conn)
    """构建基金 Agent 状态图"""
    graph = StateGraph(AgentState)

    graph.add_node("intent_recognizer", intent_recognizer)
    graph.add_conditional_edges(
        "intent_recognizer",
        route_after_intent,
        {
            "tool_selector": "tool_selector",
            "response_generator": "response_generator",
        },
    )
    graph.add_node("tool_selector", tool_selector)
    graph.add_node("data_fetcher", data_fetcher)
    graph.add_edge(START, "intent_recognizer")
    graph.add_node("analyzer", analyzer)
    graph.add_node("compliance_checker", compliance_checker)
    graph.add_node("response_generator", response_generator)

    graph.add_edge("tool_selector", "data_fetcher")
    graph.add_edge("compliance_checker", "response_generator")
    graph.add_edge("response_generator", END)

    graph.add_conditional_edges(
        "data_fetcher",
        has_fund_code,
        {"analyzer": "analyzer", "response_generator": "response_generator"},
    )
    graph.add_conditional_edges(
        "analyzer",
        should_check_compliance,
        {
            "compliance_checker": "compliance_checker",
            "response_generator": "response_generator",
        },
    )

    fund_agent_graph = graph.compile(
        checkpointer=checkpointer, interrupt_after=["compliance_checker"]
    )
    print("[状态图] 构建完成！")


def get_graph():
    """获取已初始化的状态图"""
    return fund_agent_graph

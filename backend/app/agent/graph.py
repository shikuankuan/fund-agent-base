"""Agent 状态图构建"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from app.agent.state import AgentState
from app.agent.nodes import (
    intent_recognizer,
    tool_selector,
    data_fetcher,
    analyzer,
    compliance_checker,
    response_generator,
)
from app.agent.router import route_by_intent, should_check_compliance, has_fund_code

# ========== 1. 创建 Checkpointer ==========

# 1.1 连接到 SQLite 数据库（文件：.langgraph.db）
conn = sqlite3.connect(".langgraph.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

print("✅ SqliteSaver 连接成功 → .langgraph.db")
print("   (每个节点执行完自动保存 Checkpoint)")


def build_fund_agent_graph():
    """构建基金 Agent 状态图

    流程：
    intent_recognizer → tool_selector → data_fetcher
                                           ↓
                                    has_fund_code?
                                   ├─ 是 → analyzer
                                   └─ 否 → response_generator
                                              ↓
                                   should_check_compliance?
                                   ├─ 是 → compliance_checker → response_generator → END
                                   └─ 否 → response_generator → END

    Returns:
        CompiledGraph: 编译后的状态图
    """
    # 1. 创建状态图
    graph = StateGraph(AgentState)

    # 2. 添加节点
    graph.add_node("intent_recognizer", intent_recognizer)
    graph.add_node("tool_selector", tool_selector)
    graph.add_node("data_fetcher", data_fetcher)
    graph.add_node("analyzer", analyzer)
    graph.add_node("compliance_checker", compliance_checker)
    graph.add_node("response_generator", response_generator)

    # 3. 设置入口节点
    graph.set_entry_point("intent_recognizer")

    # 4. 添加固定边
    graph.add_edge("intent_recognizer", "tool_selector")
    graph.add_edge("tool_selector", "data_fetcher")
    graph.add_edge("compliance_checker", "response_generator")
    graph.add_edge("response_generator", END)

    # 5. 添加条件边

    # data_fetcher → 有基金代码？ → analyzer / response_generator
    graph.add_conditional_edges(
        "data_fetcher",
        has_fund_code,
        {"analyzer": "analyzer", "response_generator": "response_generator"},
    )

    # analyzer → 需要合规？ → compliance_checker / response_generator
    graph.add_conditional_edges(
        "analyzer",
        should_check_compliance,
        {
            "compliance_checker": "compliance_checker",
            "response_generator": "response_generator",
        },
    )

    # 6. 编译
    app = graph.compile(checkpointer=checkpointer)

    print("[状态图] 构建完成！")
    return app


# 导出编译后的图
fund_agent_graph = build_fund_agent_graph()

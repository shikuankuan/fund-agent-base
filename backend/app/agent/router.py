"""条件路由函数"""

from app.agent.state import AgentState


def route_by_intent(state: AgentState) -> str:
    """根据意图路由到不同处理分支

    Args:
        state: 当前状态

    Returns:
        str: 下一个节点的名称
    """
    intent = state.get("user_intent", "query")

    if intent == "query":
        return "data_fetcher"
    elif intent == "analyze":
        return "data_fetcher"
    elif intent == "compare":
        return "data_fetcher"
    elif intent == "compliance":
        return "compliance_checker"
    else:
        return "response_generator"


def should_check_compliance(state: AgentState) -> str:
    """判断是否需要合规审查

    条件：
    - 有分析结果 → 必须走合规
    - 没有分析结果 → 跳过合规

    Args:
        state: 当前状态

    Returns:
        str: "compliance_checker" 或 "response_generator"
    """
    if state.get("analysis_result") is not None:
        print("[条件路由] 有分析结果，需要合规审查")
        return "compliance_checker"

    print("[条件路由] 无分析结果，跳过合规审查")
    return "response_generator"


def has_fund_code(state: AgentState) -> str:
    """判断是否有基金代码

    条件：
    - 有基金代码 → 可以进行分析
    - 没有基金代码 → 提示用户输入

    Args:
        state: 当前状态

    Returns:
        str: "analyzer" 或 "response_generator"
    """
    if state.get("current_fund") is not None:
        print(f"[条件路由] 有基金代码: {state['current_fund']}")
        return "analyzer"
    else:
        print("[条件路由] 无基金代码，提示用户输入")
        return "response_generator"

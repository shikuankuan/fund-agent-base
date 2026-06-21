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

    触发合规审查的条件（同时满足）：
    1. 意图是 compliance（用户明确问合规/风险匹配）
    2. 或 意图是 analyze/recommend 且消息包含购买意图关键词
    3. 且有分析结果可供审查

    纯查询/分析（"查净值"、"这只基金怎么样"）不走合规。
    """
    intent = state.get("user_intent", "query")

    # compliance 意图 → 必走合规
    if intent == "compliance":
        if state.get("analysis_result") is not None:
            print(f"[条件路由] compliance 意图 → 合规审查")
            return "compliance_checker"
        print(f"[条件路由] compliance 意图但无分析结果 → 跳过合规")
        return "response_generator"

    # analyze / recommend 意图 → 只有涉及购买决策时走合规
    if intent in ("analyze", "recommend"):
        user_message = state["messages"][-1].content
        buy_keywords = ["买", "购买", "申购", "认购", "下单", "买入", "适合我吗", "我能买", "可以买", "能不能买"]
        has_buy_intent = any(kw in user_message for kw in buy_keywords)

        if has_buy_intent and state.get("analysis_result") is not None:
            print(f"[条件路由] {intent} + 购买意图 → 合规审查")
            return "compliance_checker"
        else:
            print(f"[条件路由] {intent} 但无购买意图 → 跳过合规")
            return "response_generator"

    # 其他意图（query/compare/general）→ 不走合规
    print(f"[条件路由] 意图={intent}，无需合规审查")
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


def route_after_intent(state: AgentState) -> str:
    """意图识别后的条件路由
    - general → 直接生成回复（跳过所有基金逻辑）
    - 其他 → 走工具选择 → 数据获取 → ...
    """
    intent = state.get("user_intent", "query")
    if intent == "general":
        print("[条件路由] general 意图 → 直接回复（不使用基金数据）")
        return "response_generator"
    return "tool_selector"

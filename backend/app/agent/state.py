"""Agent 状态定义"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """基金 Agent 的状态

    状态字段说明：
    - messages: 对话历史（自动累加）
    - user_intent: 用户意图（query/analyze/compare/compliance）
    - current_fund: 当前处理的基金代码
    - analysis_result: 分析结果
    - compliance_result: 合规审查结果
    - final_response: 最终回复
    """

    # ========== 核心字段 ==========

    # 对话历史（使用 add_messages 自动累加）
    # Annotated 是 Python 的类型注解，add_messages 是 reducer 函数
    # 意思是：每次节点返回 messages 时，自动追加到现有列表（不是替换）
    messages: Annotated[List[BaseMessage], add_messages]

    # ========== 业务字段 ==========

    # 用户意图
    # 可选值：query（查询）、analyze（分析）、compare（对比）、compliance（合规）
    user_intent: Optional[str]

    # 当前基金代码（例如："005827"）
    current_fund: Optional[str]

    # 分析结果（字典类型）
    # 例如：{"return_1y": 0.15, "risk_level": "中高风险"}
    analysis_result: Optional[Dict[str, Any]]

    # 合规审查结果（字典类型）
    # 例如：{"is_match": False, "warning": "风险不匹配"}
    compliance_result: Optional[Dict[str, Any]]

    # 最终回复（字符串）
    final_response: Optional[str]

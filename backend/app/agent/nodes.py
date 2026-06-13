"""Agent 节点定义"""

from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
from app.agent.state import AgentState

import os

# ========== 辅助函数 ==========


def get_llm():
    """获取 LLM 实例

    返回：
    ChatOpenAI 实例（使用 Qwen3）
    """
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=0.7,
    )


# ========== 节点 1: 意图识别 ==========
def intent_recognizer(state: AgentState) -> dict:
    """识别用户意图

    意图类型：
    - query: 查询类（"000001 怎么样？"）
    - analyze: 分析类（"分析 005827 的风险"）
    - compare: 对比类（"对比 000001 和 110011"）
    - compliance: 合规类（"R3 投资者能买高风险基金吗？"）

    Args:
    state: 当前状态（包含 messages）

    Returns:
    dict: 需要更新的状态字段（这里是 user_intent）
    """
    llm = get_llm()

    # 获取用户最新消息
    # state["messages"] 是一个列表，最后一条是用户最新消息
    user_message = state["messages"][-1].content

    print(f"[意图识别] 用户消息: {user_message}")

    # 意图识别 Prompt
    # system: 给 LLM 的指令
    # user: 用户的输入
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是一个意图识别专家。分析用户消息，返回以下意图之一：
                        - query: 查询类（查基金信息、净值、经理等）
                        - analyze: 分析类（分析业绩、风险、持仓等）
                        - compare: 对比类（对比多只基金）
                        - compliance: 合规类（风险匹配、合规审查等）

                        只返回意图类型，不要返回其他内容。""",
            ),
            ("user", "{message}"),
        ]
    )

    # 构建链并执行
    # prompt | llm: 先渲染 prompt，再调用 LLM
    chain = prompt | llm
    result = chain.invoke({"message": user_message})

    # 提取意图（转小写，防止 LLM 返回大写）
    intent = result.content.strip().lower()

    print(f"[意图识别] 识别结果: {intent}")

    # 返回需要更新的状态字段
    # 注意：只返回要更新的字段，不是整个状态
    return {"user_intent": intent}


def tool_selector(state: AgentState) -> dict:
    """根据意图选择工具集

    不同意图对应不同的工具：
    - query: get_fund_info, get_fund_nav, search_funds
    - analyze: analyze_fund_performance, analyze_fund_risk
    - compare: compare_funds
    - compliance: check_risk_match, check_compliance

    Args:
    state: 当前状态（包含 user_intent）

    Returns:
    dict: 需要更新的状态字段（这里是 selected_tools）
    """
    # 获取用户意图（如果不存在，默认 query）
    intent = state.get("user_intent", "query")

    print(f"[工具选择] 意图: {intent}")

    # 工具映射表
    tool_mapping = {
        "query": [
            "get_fund_info",
            "get_fund_nav",
            "search_funds",
            "get_fund_manager_info",
        ],
        "analyze": ["analyze_fund_performance", "analyze_fund_risk", "get_fund_info"],
        "compare": ["compare_funds", "get_fund_info"],
        "compliance": ["check_risk_match", "check_compliance", "risk_disclosure"],
    }

    # 根据意图选择工具
    selected_tools = tool_mapping.get(intent, ["get_fund_info"])

    print(f"[工具选择] 选择工具: {selected_tools}")

    # 返回选择的工具列表
    return {"selected_tools": selected_tools}


# ========== 节点 3: 数据获取 ==========
def data_fetcher(state: AgentState) -> dict:
    """调用数据工具获取信息

    根据工具选择结果，调用相应的工具获取数据。

    Args:
    state: 当前状态（包含 messages）

    Returns:
    dict: 需要更新的状态字段（这里是 current_fund, fund_info）
    """
    from app.services.fund_data import FundDataService

    # 获取服务实例
    service = FundDataService()

    # 提取基金代码（从用户消息中）
    user_message = state["messages"][-1].content

    # 简单的基金代码提取（实际项目中用正则或 NER）
    import re

    fund_codes = re.findall(r"\b\d{6}\b", user_message)

    print(f"[数据获取] 用户消息: {user_message}")
    print(f"[数据获取] 提取的基金代码: {fund_codes}")

    # 如果找到基金代码
    if fund_codes:
        fund_code = fund_codes[0]
        fund_info = service.get_fund_info(fund_code)

        print(f"[数据获取] 基金代码: {fund_code}")
        print(f"[数据获取] 基金名称: {fund_info.name if fund_info else '未知'}")

        return {"current_fund": fund_code, "fund_info": fund_info}

    # 没找到基金代码
    print("[数据获取] 未找到基金代码")
    return {"current_fund": None, "fund_info": None}


# ========== 节点 4: 分析计算 ==========
def analyzer(state: AgentState) -> dict:
    """执行分析计算

    调用分析工具，计算业绩、风险等指标。

    Args:
    state: 当前状态（包含 current_fund）

    Returns:
    dict: 需要更新的状态字段（这里是 analysis_result）
    """
    from app.services.fund_data import FundDataService

    fund_code = state.get("current_fund")

    if not fund_code:
        print("[分析计算] 无基金代码，跳过分析")
        return {"analysis_result": None}

    service = FundDataService()

    # 模拟分析结果（实际项目中调用真实分析工具）
    # 这里我们先 mock 一些数据
    analysis_result = {
        "fund_code": fund_code,
        "performance": {
            "return_1y": 0.15,  # 年化收益 15%
            "return_3y": 0.45,  # 3年收益 45%
            "sharpe_ratio": 1.2,  # 夏普比率 1.2
        },
        "risk": {
            "max_drawdown": 0.12,  # 最大回撤 12%
            "volatility": 0.18,  # 波动率 18%
            "risk_level": "中高风险",  # 风险等级
        },
    }

    print(f"[分析计算] 基金代码: {fund_code}")
    print(f"[分析计算] 分析结果: {analysis_result}")

    return {"analysis_result": analysis_result}


# ========== 节点 5: 合规审查 ==========
def compliance_checker(state: AgentState) -> dict:
    """合规审查

    检查风险匹配、合规性等。

    Args:
    state: 当前状态（包含 analysis_result, messages）

    Returns:
    dict: 需要更新的状态字段（这里是 compliance_result）
    """
    from app.services.fund_data import FundDataService

    user_message = state["messages"][-1].content
    analysis_result = state.get("analysis_result", {})

    # 提取风险等级（从用户消息中）
    # 例如："检查是否适合 R3 风险等级的投资者"
    import re

    risk_levels = re.findall(r"R[1-5]", user_message)
    investor_risk = risk_levels[0] if risk_levels else "R3"

    # 获取基金风险等级
    fund_risk = analysis_result.get("risk", {}).get("risk_level", "中风险")

    # 风险等级映射（文字 → 代码）
    risk_mapping = {
        "低风险": "R1",
        "中低风险": "R2",
        "中风险": "R3",
        "中高风险": "R4",
        "高风险": "R5",
    }

    fund_risk_code = risk_mapping.get(fund_risk, "R3")

    # 判断是否匹配
    # 投资者风险等级 >= 基金风险等级 → 匹配
    investor_level = int(investor_risk[1])  # "R3" → 3
    fund_level = int(fund_risk_code[1])  # "R4" → 4

    is_match = investor_level >= fund_level

    compliance_result = {
        "investor_risk": investor_risk,
        "fund_risk": fund_risk_code,
        "is_match": is_match,
        "warning": (
            None
            if is_match
            else f"风险不匹配！投资者风险等级 {investor_risk}，基金风险等级 {fund_risk_code}"
        ),
    }

    print(f"[合规审查] 投资者风险: {investor_risk}")
    print(f"[合规审查] 基金风险: {fund_risk_code}")
    print(f"[合规审查] 匹配结果: {'匹配' if is_match else '不匹配'}")

    return {"compliance_result": compliance_result}


# ========== 节点 6: 生成回复 ==========
def response_generator(state: AgentState) -> dict:
    """生成最终回复

    根据意图、分析结果、合规结果，生成最终回复。

    Args:
    state: 当前状态（包含 user_intent, fund_info, analysis_result, compliance_result）

    Returns:
    dict: 需要更新的状态字段（这里是 final_response, messages）
    """
    llm = get_llm()

    # 从状态中获取所有相关信息
    intent = state.get("user_intent", "query")
    fund_info = state.get("fund_info")
    analysis_result = state.get("analysis_result")
    compliance_result = state.get("compliance_result")
    current_fund = state.get("current_fund")

    # 构建上下文（把所有信息整合到一起）
    context = f"""
## 用户意图
{intent}

## 基金信息
基金代码: {current_fund if current_fund else '未知'}
基金名称: {fund_info.name if fund_info else '未知'}
基金公司: {fund_info.company if fund_info else '未知'}

## 分析结果
{analysis_result if analysis_result else '无'}

## 合规结果
{compliance_result if compliance_result else '无'}
"""

    print(f"[生成回复] 上下文: {context[:200]}...")  # 只打印前 200 字符

    # 生成回复的 Prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是基金行业专业助手。根据以下信息生成专业、友好的回复：

{context}

要求：
1. 语言简洁专业，使用中文
2. 数据准确，如果数据不完整请说明
3. 如果涉及投资建议，必须包含风险提示
4. 如果合规结果显示风险不匹配，必须明确提示
5. 回复长度控制在 200-400 字
""",
            ),
            ("user", "{user_message}"),
        ]
    )

    # 获取用户最新消息
    user_message = state["messages"][-1].content

    # 生成回复
    chain = prompt | llm
    result = chain.invoke({"context": context, "user_message": user_message})

    final_response = result.content

    print(f"[生成回复] 最终回复: {final_response[:100]}...")  # 只打印前 100 字符

    # 返回最终回复 + 更新 messages（把助手回复加到对话历史）
    return {
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)],
    }

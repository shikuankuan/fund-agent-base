"""Agent 节点定义"""

from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.config import settings
from app.agent.state import AgentState
from app.agent.logger import trace_node, create_llm_logger

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
@trace_node("intent_recognizer")
def intent_recognizer(state: AgentState) -> dict:
    """识别用户意图

    意图类型：
    - query: 查询类（"000001 怎么样？"）
    - analyze: 分析类（"分析 005827 的风险"）
    - compare: 对比类（"对比 000001 和 110011"）
    - compliance: 合规类（"R3 投资者能买高风险基金吗？"）
    - recommend: 推荐类（"推荐一只基金"、"我是R4买什么"、"有什么好基金"）
    - general: 通用类（非基金问题，如"今天天气"、"讲个笑话"）

    Args:
    state: 当前状态（包含 messages）

    Returns:
    dict: 需要更新的状态字段（这里是 user_intent）
    """
    llm = get_llm()
    # 给 LLM 装上日志回调（追踪每次 LLM 调用的 token 消耗）
    llm.callbacks = [create_llm_logger("intent_recognizer")]

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
- compare: 对比类（"对比"、"比较"、"跟...比"、"vs"、"和...哪个好"、"区别"）
- compliance: 合规类（风险匹配、合规审查、"我能买吗"）
- recommend: 推荐类（"推荐"、"有什么好基金"、"R4适合买什么"、"帮我选"、"不想买...推荐"）
- general: 通用类（与基金/投资/理财完全无关的问题）

关键判断规则：
- 含"对比/比较/vs/跟...比/区别/哪个好/哪个更" → compare
- 含"推荐/不想买/帮我选/有什么/适合/买什么" → recommend
- 含"R1-R5/风险等级/能买吗" → compliance
- 含"分析/评价/怎么看/怎么样" + 有基金代码 → analyze
- 单纯"查/净值/经理/持仓" → query
- 完全不涉及基金/投资 → general

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

    # 新增：提取用户风险等级
    user_message = state["messages"][-1].content
    import re

    risk_match = re.search(r"\bR([1-5])\b", user_message)

    update = {"user_intent": intent}

    if risk_match:
        update["user_risk_level"] = f"R{risk_match.group(1)}"
        print(f"[意图识别] 检测到用户风险等级: {update['user_risk_level']}")
    # 返回需要更新的状态字段
    # 注意：只返回要更新的字段，不是整个状态
    return update


@trace_node("tool_selector")
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
@trace_node("data_fetcher")
def data_fetcher(state: AgentState) -> dict:
    """获取基金数据 - 核心原则：有代码查代码，无代码查全库

    1. 从当前消息提取基金代码（也扫描对话历史用于跨轮指代）
    2. 如果是指代追问（"它"、"这个"），自动补上上下文里的基金代码
    3. 有代码 → 全部查询，存入 all_funds
    4. 无代码 + 基金相关意图 → 查全库所有基金
    5. recommend 意图 → 查全库（排除用户不想买的代码）
    """
    from app.services.fund_data import FundDataService, FUND_DATABASE
    import re

    service = FundDataService()

    # --- 步骤1: 从当前消息提取基金代码 ---
    user_message = state["messages"][-1].content
    new_codes = re.findall(r"(?<!\d)\d{6}(?!\d)", user_message)

    # --- 步骤2: 扫描全部对话历史中的基金代码（跨轮指代用）---
    all_conv_codes = []
    for msg in state["messages"]:
        content = msg.content if hasattr(msg, "content") else ""
        for c in re.findall(r"(?<!\d)\d{6}(?!\d)", content):
            if c not in all_conv_codes:
                all_conv_codes.append(c)

    # --- 步骤3: 确定需要查询的代码 ---
    intent = state.get("user_intent", "query")
    old_current = state.get("current_fund")
    previous_fund = state.get("previous_fund")

    codes_to_fetch = set(new_codes)

    # 跨轮指代检测：消息中有"它/他/这个/那只"但没有新代码 → 用上下文中的
    referential_words = ["它", "他", "这个", "那个", "这只", "那只", "这", "那"]
    has_reference = any(w in user_message for w in referential_words)

    if has_reference and not new_codes:
        if old_current and old_current not in codes_to_fetch:
            codes_to_fetch.add(old_current)
            print(f"[数据获取] 跨轮指代 → 补上 {old_current}")

    # 对比意图 + 代码不足2只 → 尝试从上下文补全
    if intent == "compare" and len(codes_to_fetch) < 2:
        for ctx_code in [old_current, previous_fund]:
            if ctx_code and ctx_code not in codes_to_fetch:
                codes_to_fetch.add(ctx_code)
                print(f"[数据获取] compare补码 → {ctx_code}")

    codes_to_fetch = list(codes_to_fetch)
    fund_related_intents = ["query", "analyze", "compare", "recommend"]

    print(f"[数据获取] 消息: {user_message}")
    print(f"[数据获取] 当前消息代码: {new_codes} | 全部对话代码: {all_conv_codes}")
    print(f"[数据获取] 上下文: old={old_current} prev={previous_fund}")
    print(f"[数据获取] 最终查询代码: {codes_to_fetch}")

    update = {"fund_codes": new_codes}

    # --- 步骤4: 根据意图和代码情况查询 ---
    if intent == "recommend":
        # 推荐意图：查全库，排除用户明确不想要的
        all_funds = [
            service.get_fund_info(code).model_dump()
            for code in FUND_DATABASE
            if code not in codes_to_fetch
        ]
        update["all_funds"] = all_funds
        if all_funds:
            update["current_fund"] = all_funds[0]["code"]
            update["fund_info"] = service.get_fund_info(all_funds[0]["code"])
        print(f"[数据获取] recommend → 排除{codes_to_fetch}，返回{len(all_funds)}只")

    elif codes_to_fetch:
        # 有代码 → 全部查询
        all_funds = []
        for code in codes_to_fetch:
            info = service.get_fund_info(code)
            if info:
                all_funds.append(info.model_dump())
            else:
                print(f"[数据获取] ⚠️ 代码 {code} 不存在")

        update["all_funds"] = all_funds
        update["current_fund"] = codes_to_fetch[0]
        update["fund_info"] = service.get_fund_info(codes_to_fetch[0])
        print(f"[数据获取] 查询{len(codes_to_fetch)}只 → 命中{len(all_funds)}只")

    elif intent in fund_related_intents:
        # 无代码 + 基金意图 → 查全库
        all_funds = [service.get_fund_info(code).model_dump() for code in FUND_DATABASE]
        update["all_funds"] = all_funds
        if all_funds:
            update["current_fund"] = all_funds[0]["code"]
            update["fund_info"] = service.get_fund_info(all_funds[0]["code"])
        print(f"[数据获取] 无代码+基金意图 → 全库{len(all_funds)}只")

    elif old_current:
        # 兜底：非基金意图但有上下文，沿用
        info = service.get_fund_info(old_current)
        update["current_fund"] = old_current
        update["fund_info"] = info
        if info:
            update["all_funds"] = [info.model_dump()]
        print(f"[数据获取] 沿用上下文: {old_current}")

    # --- 步骤5: 如果换了基金 → 保存旧值 ---
    new_current = update.get("current_fund")
    if old_current and new_current and old_current != new_current:
        update["previous_fund"] = old_current
        update["previous_fund_info"] = state.get("fund_info")
        update["previous_analysis"] = state.get("analysis_result")
        print(f"[数据获取] 换基金: {old_current} → {new_current}")

    fi = update.get("fund_info")
    fi_name = (
        fi.name
        if hasattr(fi, "name")
        else (fi.get("name", "?") if isinstance(fi, dict) else "?")
    )
    print(
        f"[数据获取] ✓ current={new_current}({fi_name}) | all_funds={len(update.get('all_funds', []))}只"
    )
    return update


# ========== 节点 4: 分析计算 ==========
@trace_node("analyzer")
def analyzer(state: AgentState) -> dict:
    """执行分析计算 — 从 fund_info / all_funds 读取真实数据"""

    fund_info = state.get("fund_info")
    all_funds = state.get("all_funds", [])
    intent = state.get("user_intent", "query")

    if not fund_info:
        print("[分析计算] 无基金数据，跳过分析")
        return {"analysis_result": None}

    # 提取当前基金数据的辅助函数
    def extract_analysis(info):
        if info is None:
            return None
        d = info.model_dump() if hasattr(info, "model_dump") else info
        nav = d.get("nav", {}) or {}
        risk = d.get("risk_metrics", {}) or {}
        mgr = d.get("manager", {}) or {}
        return {
            "fund_code": d.get("code"),
            "fund_name": d.get("name"),
            "performance": {
                "return_1w": nav.get("weekly_change", 0),
                "return_1m": nav.get("monthly_change", 0),
                "return_1y": nav.get("yearly_change", 0),
                "sharpe_ratio": risk.get("sharpe_ratio", 0),
            },
            "risk": {
                "max_drawdown": risk.get("max_drawdown", 0),
                "volatility": risk.get("volatility", 0),
                "beta": risk.get("beta", 0),
                "alpha": risk.get("alpha", 0),
                "risk_level": d.get("risk_level", "中风险"),
            },
            "manager": {
                "name": mgr.get("name", ""),
                "tenure_years": mgr.get("tenure_years", 0),
                "style": mgr.get("investment_style", ""),
            },
        }

    analysis_result = extract_analysis(fund_info)

    # 对比意图：分析 all_funds 中的所有基金
    if intent == "compare" and len(all_funds) >= 2:
        analysis_result["comparison"] = []
        for f in all_funds:
            fd = (
                extract_analysis(f)
                if not hasattr(f, "model_dump")
                else extract_analysis(f)
            )
            # 如果 f 已经是 dict
            if isinstance(f, dict):
                nav = f.get("nav", {}) or {}
                risk = f.get("risk_metrics", {}) or {}
                mgr = f.get("manager", {}) or {}
                analysis_result["comparison"].append(
                    {
                        "code": f.get("code"),
                        "name": f.get("name"),
                        "company": f.get("company"),
                        "type": f.get("type"),
                        "risk_level": f.get("risk_level"),
                        "nav": nav.get("nav"),
                        "return_1y": nav.get("yearly_change"),
                        "sharpe": risk.get("sharpe_ratio"),
                        "max_drawdown": risk.get("max_drawdown"),
                        "manager": mgr.get("name"),
                    }
                )
            else:
                fd = extract_analysis(f)
                if fd:
                    analysis_result["comparison"].append(
                        {
                            "code": fd.get("fund_code"),
                            "name": fd.get("fund_name"),
                            "risk_level": fd.get("risk", {}).get("risk_level"),
                        }
                    )

    print(
        f"[分析计算] 基金: {analysis_result.get('fund_code')} | 风险: {analysis_result.get('risk', {}).get('risk_level')}"
    )
    print(f"[分析计算] 对比基金数: {len(analysis_result.get('comparison', []))}")
    return {"analysis_result": analysis_result}


# ========== 节点 5: 合规审查 ==========
@trace_node("compliance_checker")
def compliance_checker(state: AgentState) -> dict:
    print(f"[合规审查] ⚠️ 我被调用了！！！")
    """合规审查 - 多维检测 + 分级裁决

    四道检测：
    ① 敏感词检测    → 承诺收益/保本/稳赚等      severity: block
    ② 风险匹配检测  → 投资者等级 vs 基金风险     severity: block
    ③ 数据完整性    → analysis_result 字段齐全   severity: warn
    ④ 内容合规      → 预测未来/夸大宣传          severity: block

    Returns:
        {"compliance_result": {grade, checks, overall_passed, ...}}
    """
    analysis_result = state.get("analysis_result") or {}
    user_message = state["messages"][-1].content

    # ============================================================
    # 检查 ①：敏感词检测
    # ============================================================
    # block 级词汇（承诺收益类）—— 红线
    BLOCK_WORDS = [
        "guaranteed收益",
        "保证收益",
        "稳赚",
        "保本",
        "零风险",
        "无风险",
        "包赚",
        "绝对收益",
        "固定收益",
        "稳赢",
        "百分百赚",
        "确定收益",
        "锁定收益",
    ]
    # warn 级词汇（暗示性表述）
    WARN_WORDS = [
        "大概率赚",
        "基本不会亏",
        "历史最低点",
        "最佳时机",
        "一定涨",
        "必涨",
    ]

    # 检查用户消息
    user_block_hits = [w for w in BLOCK_WORDS if w in user_message]
    user_warn_hits = [w for w in WARN_WORDS if w in user_message]

    sensitive_passed = len(user_block_hits) == 0 and len(user_warn_hits) == 0
    sensitive_severity = (
        "block" if user_block_hits else "warn" if user_warn_hits else "pass"
    )
    sensitive_check = {
        "name": "敏感词检测",
        "passed": sensitive_passed,
        "severity": sensitive_severity,
        "block_hits": user_block_hits,
        "warn_hits": user_warn_hits,
        "detail": (
            f"发现敏感词: {', '.join(user_block_hits + user_warn_hits)}"
            if not sensitive_passed
            else "通过"
        ),
    }
    print(
        f"[合规审查] ① 敏感词: {'通过' if sensitive_passed else '命中 ' + str(user_block_hits + user_warn_hits)}"
    )

    # ============================================================
    # 检查 ②：风险匹配检测
    # ============================================================
    # 优先用状态里已有的 user_risk_level（跨轮对话保存的）
    investor_risk = state.get("user_risk_level")
    if not investor_risk:
        # 兜底：从当前消息提取
        import re

        risk_levels = re.findall(r"R[1-5]", user_message)
        investor_risk = risk_levels[0] if risk_levels else "R3"

    # 从 fund_info 读取真实风险等级（比 analysis_result 更可靠）
    fund_info = state.get("fund_info")
    fund_risk_label = "中风险"
    if fund_info is not None:
        d = fund_info.model_dump() if hasattr(fund_info, "model_dump") else fund_info
        fund_risk_label = d.get("risk_level", "中风险")
    elif isinstance(analysis_result, dict):
        fund_risk = analysis_result.get("risk", {})
        fund_risk_label = (
            fund_risk.get("risk_level", "中风险")
            if isinstance(fund_risk, dict)
            else "中风险"
        )

    risk_mapping = {
        "低风险": "R1",
        "中低风险": "R2",
        "中风险": "R3",
        "中高风险": "R4",
        "高风险": "R5",
    }
    fund_risk_code = risk_mapping.get(fund_risk_label, "R3")

    investor_level = int(investor_risk[1])
    fund_level = int(fund_risk_code[1])
    risk_passed = investor_level >= fund_level
    risk_severity = "pass" if risk_passed else "block"

    risk_check = {
        "name": "风险匹配检测",
        "passed": risk_passed,
        "severity": risk_severity,
        "investor_risk": investor_risk,
        "fund_risk": fund_risk_code,
        "detail": (
            f"匹配"
            if risk_passed
            else f"不匹配！投资者 {investor_risk}，基金 {fund_risk_code}"
        ),
    }
    print(f"[合规审查] ② 风险匹配: {risk_check['detail']}")

    # ============================================================
    # 检查 ③：数据完整性
    # ============================================================
    missing_fields = []
    if not analysis_result.get("returns"):
        missing_fields.append("收益率数据")
    if not analysis_result.get("risk"):
        missing_fields.append("风险指标")
    if not analysis_result.get("manager"):
        missing_fields.append("基金经理信息")

    data_passed = len(missing_fields) == 0
    data_check = {
        "name": "数据完整性",
        "passed": data_passed,
        "severity": "pass" if data_passed else "warn",
        "missing": missing_fields,
        "detail": ("数据完整" if data_passed else f"缺少: {', '.join(missing_fields)}"),
    }
    print(f"[合规审查] ③ 数据: {data_check['detail']}")

    # ============================================================
    # 检查 ④：内容合规（检查 analysis_result 是否有预测性表述）
    # ============================================================
    analysis_str = str(analysis_result)
    prediction_keywords = [
        "预测",
        "预计",
        "未来将",
        "后市必",
        "一定会涨",
        "明天必",
        "即将暴涨",
        "即将大跌",
    ]
    prediction_hits = [w for w in prediction_keywords if w in analysis_str]
    content_passed = len(prediction_hits) == 0

    content_check = {
        "name": "内容合规",
        "passed": content_passed,
        "severity": "pass" if content_passed else "block",
        "hits": prediction_hits,
        "detail": (
            "通过"
            if content_passed
            else f"发现预测性/夸大性表述: {', '.join(prediction_hits)}"
        ),
    }
    print(f"[合规审查] ④ 内容: {content_check['detail']}")

    # ============================================================
    # 汇总 → 分级
    # ============================================================
    all_checks = [sensitive_check, risk_check, data_check, content_check]

    # 取最高严重级别
    severities = [c["severity"] for c in all_checks]
    if "block" in severities:
        grade = "block"
    elif "warn" in severities:
        grade = "warn"
    else:
        grade = "pass"

    overall_passed = grade == "pass"

    compliance_result = {
        "grade": grade,
        "overall_passed": overall_passed,
        "checks": all_checks,
        # 兼容旧字段
        "investor_risk": investor_risk,
        "fund_risk": fund_risk_code,
        "is_match": risk_passed,
        "warning": None if risk_passed else f"风险不匹配！",
    }

    print(
        f"[合规审查] 🏁 最终评级: {grade} | {'✅ 通过' if overall_passed else '⚠️ 需审批'}"
    )
    return {"compliance_result": compliance_result}


# ========== 节点 6: 生成回复 ==========
@trace_node("response_generator")
def response_generator(state: AgentState) -> dict:
    """生成最终回复

    根据意图、分析结果、合规结果，生成最终回复。
    如果提供了全库基金列表，根据用户意图从中筛选推荐；
    如果用户问R4，找出风险等级匹配的基金重点推荐

    Args:
    state: 当前状态（包含 user_intent, fund_info, analysis_result, compliance_result）

    Returns:
    dict: 需要更新的状态字段（这里是 final_response, messages）
    """
    llm = get_llm()
    # 给 LLM 装上日志回调（追踪每次 LLM 调用的 token 消耗）
    llm.callbacks = [create_llm_logger("response_generator")]

    # 从状态中获取所有相关信息
    intent = state.get("user_intent", "query")
    fund_info = state.get("fund_info")
    previous_fund_info = state.get("previous_fund_info")
    analysis_result = state.get("analysis_result")
    compliance_result = state.get("compliance_result")
    current_fund = state.get("current_fund")
    previous_fund = state.get("previous_fund")

    # ✅ 统一提取函数：兼容 Pydantic 对象(dict 序列化后) 和原始 dict
    def _extract(fi):
        if fi is None:
            return "未知", "未知", "", ""
        if hasattr(fi, "model_dump"):
            d = fi.model_dump()
        elif hasattr(fi, "dict"):
            d = fi.dict()
        else:
            d = fi if isinstance(fi, dict) else {}
        if not isinstance(d, dict):
            return "未知", "未知", "", ""
        name = d.get("name", "未知")
        company = d.get("company", "未知")
        mgr = d.get("manager", {}) or {}
        manager = (
            mgr.get("name", "")
            if isinstance(mgr, dict)
            else (mgr.name if hasattr(mgr, "name") else "")
        )
        risk = d.get("risk_level", "")
        return name, company, manager, risk

    fund_name, fund_company, fund_manager, fund_risk = _extract(fund_info)
    print(
        f"[生成回复] fund={fund_name} | company={fund_company} | manager={fund_manager} | risk={fund_risk}"
    )
    # 构建上一只基金的上下文
    prev_fund_context = ""
    if previous_fund:
        prev_name, prev_company, prev_manager, prev_risk = _extract(previous_fund_info)
        prev_fund_context = f"""
## 上一轮讨论的基金（用于对比）
代码: {previous_fund} | 名称: {prev_name} | 公司: {prev_company}
经理: {prev_manager} | 风险: {prev_risk}"""

    # 构建全库基金列表（带上关键信息）
    all_funds_context = ""
    all_funds_list = state.get("all_funds")
    if all_funds_list:
        lines = ["## 可用的完整基金列表（共 {} 只）\n".format(len(all_funds_list))]
        for f in all_funds_list:
            d = (
                f
                if isinstance(f, dict)
                else (f.model_dump() if hasattr(f, "model_dump") else {})
            )
            nav = d.get("nav", {}) or {}
            risk_metrics = d.get("risk_metrics", {}) or {}
            mgr = d.get("manager", {}) or {}
            lines.append(
                f"- **{d.get('code')}** {d.get('name')} | {d.get('type')} | {d.get('risk_level')} | "
                f"{d.get('company')} | 经理: {mgr.get('name','?')}({mgr.get('tenure_years','?')}年) | "
                f"规模: {d.get('scale','?')} | "
                f"近1年: {nav.get('yearly_change','?')}% | "
                f"夏普: {risk_metrics.get('sharpe_ratio','?')} | "
                f"最大回撤: {risk_metrics.get('max_drawdown','?')}% | "
                f"简介: {d.get('description','')}"
            )
        all_funds_context = "\n".join(lines)

    # 构建上下文（把所有信息整合到一起）
    context = f"""
## 用户意图
{intent}

## 基金信息
基金代码: {current_fund if current_fund else '未知'}
当前基金名称: {fund_name}
基金公司: {fund_company}
基金经理: {fund_manager}
{prev_fund_context}
{all_funds_context}

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
                """你是专业基金投顾助手。根据「上下文」中的基金数据回答用户问题。

{context}

## 核心规则
1. **数据驱动**：回答必须基于上下文提供的真实数据，不要编造
2. **对比场景**：如果上下文有「全库基金列表」，逐一对比分析各基金
3. **推荐场景**：如果上下文有「全库基金列表」，从中筛选匹配用户需求的基金
4. **风险匹配**：如果合规结果显示风险不匹配，必须明确警告用户
5. **使用真实数据**：引用数据时使用上下文中提供的数值，不要用占位符
6. **如果数据真的缺失**：诚实说明某只基金的哪些数据暂不可用，同时建议用户查看可用数据

## 回复格式
- 语言简洁专业，使用中文
- **对比或列举场景必须用 markdown 表格**（| 列1 | 列2 | 格式），表头放代码/名称/类型/风险/规模/经理等字段
- 非表格内容用自然语言简要描述趋势或风险
- 涉及投资建议必须附带风险提示
- 回复长度 200-500 字

## 数据卡片嵌入规则（必须遵守）

根据对话意图，在回复末尾嵌入对应的卡片标签：

### 单基金查询（净值/持仓/风险/信息）
- 净值走势：`<fund-nav-card code="XXXXXX"/>`
- 基础信息：`<fund-info-card code="XXXXXX"/>`
- 持仓分析：`<fund-holdings-card code="XXXXXX"/>`
- 风险指标：`<fund-risk-card code="XXXXXX"/>`

### 多基金对比（最高优先级）
- 当用户意图为 compare（对比/比较/vs/哪个好/区别）时，必须在回复末尾嵌入对比卡片
- 格式：`<fund-compare-card codes="代码1,代码2,代码3"/>`
- 把所有参与对比的基金代码用英文逗号拼在一起，例如 `<fund-compare-card codes="000001,005827,110011"/>`
- **不要写硬编码的 000001，要使用上下文中实际被对比的基金代码**

**卡片标签必须独占一行，前后不能加任何无关文字。每条标签独占一行。**""",
            ),
            MessagesPlaceholder(variable_name="history"),
        ]
    )

    # 获取用户最新消息
    history = state["messages"][-10:]

    # 生成回复
    chain = prompt | llm
    result = chain.invoke({"context": context, "history": history})

    final_response = result.content

    print(f"[生成回复] 最终回复: {final_response[:100]}...")  # 只打印前 100 字符

    # 返回最终回复 + 更新 messages（把助手回复加到对话历史）
    return {
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)],
    }

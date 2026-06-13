# app/tools/compliance_tools.py
"""合规类工具：适当性匹配、合规审查、风险提示"""

from langchain_core.tools import tool
from app.services.fund_data import fund_data_service
from app.models.fund_models import FundInfo

# 风险等级映射
RISK_LEVEL_MAP = {
    "R1": 1,  # 低风险
    "R2": 2,  # 中低风险
    "R3": 3,  # 中风险
    "R4": 4,  # 中高风险
    "R5": 5,  # 高风险
}

# 违规用语清单
FORBIDDEN_WORDS = [
    "保证收益",
    " guaranteed return",
    "无风险",
    "100%收益",
    "稳赚不赔",
    "保本保息",
    "零风险",
    "绝对收益",
]


@tool(parse_docstring=True)
def check_risk_match(user_risk_level: str, fund_risk_level: str) -> str:
    """当用户询问适当性匹配时触发（例如："我是C3型投资者，XX基金（R4）适合我吗？"、"我的风险等级是C2，能买R3的基金吗？"）。

    根据《证券期货投资者适当性管理办法》，
    检查投资者风险承受能力与基金风险等级是否匹配。

    Args:
        user_risk_level: 投资者风险承受能力等级，取值为 "C1"、"C2"、"C3"、"C4"、"C5" 中的一个。从用户输入中提取，例如 "我是C3型投资者" 应提取为 "C3"。
        fund_risk_level: 基金产品风险等级，取值为 "R1"、"R2"、"R3"、"R4"、"R5" 中的一个。从用户输入中提取，例如 "XX基金（R4）" 应提取为 "R4"。

    Returns:
        适当性匹配结果（匹配/不匹配 + 原因）
    """
    print("========触发了 check_risk_match 工具")
    # 验证输入
    if not user_risk_level.startswith("C") or not fund_risk_level.startswith("R"):
        return "❌ 输入格式错误，应为 'C1'-'C5' 和 'R1'-'R5'"

    user_level = int(user_risk_level[1:])
    fund_level = RISK_LEVEL_MAP.get(fund_risk_level)

    if not fund_level:
        return f"❌ 无效的基金风险等级：{fund_risk_level}"

    # 适当性匹配规则：用户等级 >= 基金等级
    is_match = user_level >= fund_level

    # 格式化输出
    result = f"⚖️ **您的适当性匹配检查**\n\n"
    result += f"**投资者风险等级**：{user_risk_level}\n"
    result += f"**基金风险等级**：{fund_risk_level}\n\n"

    if is_match:
        result += f"✅ **匹配**\n\n"
        result += f"投资者风险承受能力（{user_risk_level}）大于或等于基金风险等级（{fund_risk_level}），符合适当性要求。\n"
    else:
        result += f"❌ **不匹配**\n\n"
        result += f"投资者风险承受能力（{user_risk_level}）低于基金风险等级（{fund_risk_level}），不符合适当性要求。\n"
        result += f"\n**建议**：请选择风险等级 ≤ {user_risk_level} 的基金产品。\n"

    return result


@tool(parse_docstring=True)
def check_compliance(content: str) -> str:
    """当用户要求合规审查时触发（例如："检查这段内容是否合规"、"这段话符合合规要求吗？"）。

    根据中国证监会《证券投资基金销售管理办法》，
    检测内容是否包含违规用语（保证收益、无风险等）。

    Args:
        content: 待检测内容（文本）

    Returns:
        合规审查结果（通过/不通过 + 违规用语列表）
    """
    if not content:
        return "❌ 请提供待检测内容"

    # 检测违规用语
    found_violations = []
    for word in FORBIDDEN_WORDS:
        if word in content:
            found_violations.append(word)

    # 格式化输出
    result = f"📋 **合规审查**\n\n"
    result += f"**检测内容**：{content[:100]}...\n\n"

    if not found_violations:
        result += f"✅ **合规通过**\n\n"
        result += f"未发现违规用语，内容符合合规要求。\n"
    else:
        result += f"❌ **合规不通过**\n\n"
    result += f"**发现 {len(found_violations)} 处违规用语**：\n"
    for i, word in enumerate(found_violations, 1):
        result += f"{i}. {word}\n"

    result += f"\n**整改建议**：\n"
    result += f"- 删除或替换违规用语\n"
    result += f"- 使用合规用语：'历史业绩'、'过往表现'、'业绩比较基准'\n"

    return result


@tool(parse_docstring=True)
def risk_disclosure(fund_code: str) -> str:
    """当用户要求生成风险提示书时触发（例如："生成XX基金的风险提示书"、"我需要XX基金的风险披露"）。

    根据中国证监会《证券投资基金信息披露管理办法》，
    生成符合监管要求的风险提示书。

    Args:
        fund_code: 基金代码，例如 "000001", "005827"

    Returns:
        风险提示书（标准模板 + 基金特定风险）
    """
    fund_info: FundInfo = fund_data_service.get_fund_info(fund_code)

    if not fund_info:
        return f"❌ 未找到基金代码 {fund_code} 的信息"

    # 标准风险提示语句
    standard_disclaimer = """**风险提示**：
 
1. 投资基金可能面临市场风险、信用风险、流动性风险等多种风险。
2. 基金管理人过往业绩不代表未来表现，不构成对基金业绩的保证。
3. 投资者应根据自身风险承受能力，谨慎选择基金产品。
4. 本基金不保证本金安全，不承诺最低收益。
5. 投资有风险，入市需谨慎。
"""

    # 基金特定风险（根据基金类型）
    fund_specific_risks = {
        "股票型": "- 股票型基金的净值波动较大，可能面临较大的市场风险。\n- 行业集中度风险：部分行业可能面临政策风险、周期风险。\n",
        "混合型": "- 混合型基金的风险收益特征介于股票型和债券型之间。\n- 资产配置风险：股债配置比例变化可能影响基金风险收益特征。\n",
        "债券型": "- 债券型基金可能面临利率风险、信用风险、流动性风险。\n- 可转债风险：部分债券型基金可能投资可转债，面临转股风险。\n",
    }

    specific_risk = fund_specific_risks.get(
        fund_info.type, "- 本基金可能面临市场风险、流动性风险等常规风险。\n"
    )

    # 格式化输出
    result = f"⚠️ **风险提示书 - {fund_info.name} ({fund_code})**\n\n"
    result += f"**基金类型**：{fund_info.type}\n"
    result += f"**风险等级**：{fund_info.risk_level}\n\n"

    result += standard_disclaimer

    result += f"\n**本基金特定风险**：\n"
    result += specific_risk

    result += f"\n**风险指标参考**：\n"
    result += f"- 夏普比率：{fund_info.risk_metrics.sharpe_ratio}\n"
    result += f"- 最大回撤：{fund_info.risk_metrics.max_drawdown}%\n"
    result += f"- 波动率：{fund_info.risk_metrics.volatility}%\n"

    result += f"\n---\n"
    result += f"*本风险提示书根据中国证监会《证券投资基金信息披露管理办法》编制，仅供参考，不构成投资建议。*\n"

    return result

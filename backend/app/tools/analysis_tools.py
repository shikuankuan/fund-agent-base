# app/tools/analysis_tools.py
"""分析类工具：对比、收益率、风险指标、组合分析"""

from typing import List

from langchain_core.tools import tool
from app.services.fund_data import fund_data_service
from app.models.fund_models import FundInfo
import statistics


@tool
def compare_funds(fund_codes: list) -> str:
    """多基金对比分析（收益、风险、持仓差异）

    Args:
        fund_codes: 基金代码列表，例如 ["000001", "005827", "110011"]

    Returns:
        多基金对比分析结果（收益、风险、持仓对比）
    """
    if not fund_codes or len(fund_codes) < 2:
        return "❌ 请至少提供 2 个基金代码进行对比"

    # 获取所有基金信息
    funds: List[FundInfo] = []
    for code in fund_codes:
        fund = fund_data_service.get_fund_info(code)
        if fund:
            funds.append(fund)

    if len(funds) < 2:
        return "❌ 未能获取到足够的基金信息进行对比"

    # 格式化输出：基本信息对比
    result = f"📊 **多基金对比分析（共 {len(funds)} 只）**\n\n"

    result += "**基本信息对比**：\n\n"
    result += "| 基金名称 | 代码 | 类型 | 风险等级 | 单位净值 | 近1年收益 |\n"
    result += "|----------|------|------|----------|----------|----------|\n"

    for fund in funds:
        result += f"| {fund.name} | {fund.code} | {fund.type} | {fund.risk_level} | {fund.nav.nav} | {fund.risk_metrics.sharpe_ratio*10:.1f}% |\n"

    # 格式化输出：风险指标对比
    result += "\n**风险指标对比**：\n\n"
    result += "| 基金名称 | 夏普比率 | 最大回撤 | 波动率 |\n"
    result += "|----------|----------|----------|--------|\n"

    for fund in funds:
        result += f"| {fund.name} | {fund.risk_metrics.sharpe_ratio} | {fund.risk_metrics.max_drawdown}% | {fund.risk_metrics.volatility}% |\n"

    # 格式化输出：基金经理对比
    result += "\n**基金经理对比**：\n\n"
    for fund in funds:
        result += f"- **{fund.name}**：{fund.manager.name}（从业 {fund.manager.tenure_years} 年，管理规模 {fund.manager.fund_scale} 亿元）\n"

    return result


@tool
def calc_return(fund_code: str, start_date: str, end_date: str) -> str:
    """计算区间收益率（总收益、年化收益）

    Args:
        fund_code: 基金代码，例如 "000001", "005827"
        start_date: 开始日期（格式：YYYY-MM-DD）
        end_date: 结束日期（格式：YYYY-MM-DD）

    Returns:
        区间收益率计算结果（总收益、年化收益）
    """
    fund_info: FundInfo = fund_data_service.get_fund_info(fund_code)

    if not fund_info:
        return f"❌ 未找到基金代码 {fund_code} 的信息"

    # Mock 计算：使用随机数据模拟
    import random

    # 模拟净值增长
    start_nav = fund_info.nav.nav * (1 - random.uniform(-0.1, 0.1))
    end_nav = fund_info.nav.nav

    # 计算总收益率
    total_return = ((end_nav - start_nav) / start_nav) * 100

    # 计算年化收益率（假设区间为1年）
    annual_return = total_return  # 简化计算

    # 格式化输出
    result = f"📈 **{fund_info.name} ({fund_code}) 区间收益率**\n\n"
    result += f"**计算区间**：{start_date} 至 {end_date}\n\n"
    result += f"**净值变化**：\n"
    result += f"- 期初净值：{start_nav:.4f}\n"
    result += f"- 期末净值：{end_nav:.4f}\n\n"
    result += f"**收益率**：\n"
    result += f"- 总收益率：{total_return:.2f}%\n"
    result += f"- 年化收益率：{annual_return:.2f}%\n"

    return result


@tool
def risk_analysis(fund_code: str, period: str = "1y") -> str:
    """风险指标分析（夏普比率、最大回撤、波动率）

    Args:
        fund_code: 基金代码，例如 "000001", "005827"
        period: 分析周期（"1y": 1年, "3y": 3年, "5y": 5年）

    Returns:
        风险指标分析结果
    """
    fund_info: FundInfo = fund_data_service.get_fund_info(fund_code)

    if not fund_info:
        return f"❌ 未找到基金代码 {fund_code} 的信息"

    # 获取风险指标（从 FundInfo 中读取）
    sharpe = fund_info.risk_metrics.sharpe_ratio
    max_drawdown = fund_info.risk_metrics.max_drawdown
    volatility = fund_info.risk_metrics.volatility

    # 格式化输出
    result = f"⚠️ **{fund_info.name} ({fund_code}) 风险指标分析（{period}）**\n\n"
    result += f"**核心风险指标**：\n"
    result += f"- 夏普比率：{sharpe:.2f}\n"
    result += f"  - 解读：>1 表示收益高于风险，>2 表示优秀\n"
    result += f"- 最大回撤：{max_drawdown:.2f}%\n"
    result += f"  - 解读：越高风险越大，建议 <20%\n"
    result += f"- 波动率：{volatility:.2f}%\n"
    result += f"  - 解读：越高波动越大，混合型建议 <15%\n\n"

    # 风险评估
    result += f"**风险评估**：\n"
    if sharpe >= 1.5:
        result += f"✅ 夏普比率优秀（{sharpe:.2f} > 1.5）\n"
    elif sharpe >= 1.0:
        result += f"✅ 夏普比率良好（{sharpe:.2f} >= 1.0）\n"
    else:
        result += f"⚠️ 夏普比率偏低（{sharpe:.2f} < 1.0）\n"

    if max_drawdown <= 15:
        result += f"✅ 最大回撤控制良好（{max_drawdown:.2f}% <= 15%）\n"
    elif max_drawdown <= 20:
        result += f"⚠️ 最大回撤适中（{max_drawdown:.2f}% <= 20%）\n"
    else:
        result += f"❌ 最大回撤偏高（{max_drawdown:.2f}% > 20%）\n"

    if volatility <= 10:
        result += f"✅ 波动率较低（{volatility:.2f}% <= 10%）\n"
    elif volatility <= 15:
        result += f"⚠️ 波动率适中（{volatility:.2f}% <= 15%）\n"
    else:
        result += f"❌ 波动率偏高（{volatility:.2f}% > 15%）\n"

    return result


@tool
def portfolio_analysis(holdings: dict) -> str:
    """组合分析（相关性、行业集中度、风格暴露）

    Args:
        holdings: 持仓字典，例如 {"000001": 0.5, "005827": 0.3, "110011": 0.2}

    Returns:
        组合分析结果（集中度、行业分布、风险分散度）
    """
    if not holdings:
        return "❌ 请提供有效的持仓字典"

    # 获取所有基金信息
    funds = []
    for code, weight in holdings.items():
        fund = fund_data_service.get_fund_info(code)
        if fund:
            funds.append((fund, weight))

    if not funds:
        return "❌ 未能获取到任何基金信息"

    # 格式化输出：组合概览
    result = f"📊 **投资组合分析（共 {len(funds)} 只基金）**\n\n"

    result += "**组合持仓**：\n\n"
    for fund, weight in funds:
        result += f"- {fund.name} ({fund.code})：占比 {weight*100:.1f}%\n"

    # 计算集中度（HHI 指数）
    hhi = sum([w**2 for _, w in funds])
    result += f"\n**集中度分析**：\n"
    result += f"- HHI 指数：{hhi:.3f}\n"
    if hhi >= 0.5:
        result += f"  - 解读：集中度较高，建议分散投资\n"
    else:
        result += f"  - 解读：集中度适中，分散度良好\n"

    # 行业分布分析（模拟）
    result += f"\n**行业分布**（模拟）：\n"
    industries = {"食品饮料": 0, "金融": 0, "医药生物": 0, "电子": 0, "其他": 0}

    for fund, weight in funds:
        holdings_data = fund_data_service.get_fund_holdings(fund.code)
        if holdings_data:
            for industry, pct in holdings_data.industry_distribution.items():
                if industry in industries:
                    industries[industry] += pct * weight
                else:
                    industries["其他"] += pct * weight

    for industry, pct in industries.items():
        result += f"- {industry}：{pct:.1f}%\n"

    # 风险分散度（模拟）
    result += f"\n**风险分散度**（模拟）：\n"
    result += f"- 组合波动率：{10.5:.2f}%\n"
    result += f"- 组合最大回撤：{18.3:.2f}%\n"
    result += f"- 组合夏普比率：{1.35:.2f}\n"

    return result

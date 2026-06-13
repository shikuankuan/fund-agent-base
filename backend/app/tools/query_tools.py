# app/tools/query_tools.py
"""查询类工具：基金信息、净值、排名、持仓、经理、搜索"""

from langchain_core.tools import tool
from app.services.fund_data import fund_data_service
from app.models.fund_models import FundInfo, FundManager, FundHoldings


@tool
def get_fund_info(fund_code: str) -> str:
    """查询基金基本信息（类型、规模、成立日期、风险等级等）

    Args:
        fund_code: 基金代码，例如 "000001", "005827"

    Returns:
        基金的详细信息（名称、代码、类型、风险等级、规模、基金经理等）
    """
    fund_info: FundInfo = fund_data_service.get_fund_info(fund_code)

    if not fund_info:
        return f"❌ 未找到基金代码 {fund_code} 的信息"

    # 格式化输出
    result = f"""📊 **{fund_info.name} ({fund_info.code})**

**基本信息**：
- 基金类型：{fund_info.type}
- 风险等级：{fund_info.risk_level}
- 基金规模：{fund_info.scale} 亿元

**基金经理**：
- 姓名：{fund_info.manager.name}
- 从业年限：{fund_info.manager.tenure_years} 年
- 投资风格：{fund_info.manager.investment_style}

**最新净值**：
- 单位净值：{fund_info.nav.nav}
- 日涨跌幅：{fund_info.nav.daily_change}%

**风险指标**：
- 夏普比率：{fund_info.risk_metrics.sharpe_ratio}
- 最大回撤：{fund_info.risk_metrics.max_drawdown}%
- 波动率：{fund_info.risk_metrics.volatility}%
"""

    return result


@tool
def get_fund_nav(fund_code: str, date_range: str = "1m") -> str:
    """查询基金净值走势（日/周/月频）

    Args:
        fund_code: 基金代码，例如 "000001", "005827"
        date_range: 时间范围（"1w": 1周, "1m": 1个月, "3m": 3个月, "6m": 6个月, "1y": 1年）

    Returns:
        基金净值走势数据
    """
    nav_history = fund_data_service.get_fund_nav_history(fund_code, date_range)

    if not nav_history:
        return f"❌ 未找到基金代码 {fund_code} 的净值数据"

    # 格式化输出（显示最近10条）
    result = f"📈 **{fund_code} 净值走势（{date_range}）**\n\n"
    result += f"共 {len(nav_history)} 条数据，显示最近 10 条：\n\n"

    for record in nav_history[-10:]:
        result += f"📅 {record['date']} | 单位净值：{record['nav']} | 涨跌幅：{record['change']}%\n"

    # 计算统计信息
    latest_nav = nav_history[-1]["nav"]
    oldest_nav = nav_history[0]["nav"]
    total_return = ((latest_nav - oldest_nav) / oldest_nav) * 100

    result += f"\n**统计信息**：\n"
    result += f"- 区间收益率：{total_return:.2f}%\n"
    result += f"- 最新净值：{latest_nav}\n"

    return result


@tool
def get_fund_ranking(
    category: str = None, sort_by: str = "nav", limit: int = 10
) -> str:
    """查询基金排名（同类排名、涨幅排行）

    Args:
        category: 基金类型（"股票型", "混合型", "债券型"，留空表示全部）
        sort_by: 排序字段（"nav": 单位净值, "return_1y": 近1年收益, "return_3y": 近3年收益）
        limit: 返回数量（默认 10）

    Returns:
        基金排名列表
    """
    rankings = fund_data_service.get_fund_ranking(category, sort_by, limit)

    if not rankings:
        return f"❌ 未找到符合条件的基金排名"

    # 格式化输出
    category_str = category if category else "全部"
    sort_str = {
        "nav": "单位净值",
        "return_1y": "近1年收益",
        "return_3y": "近3年收益",
    }.get(sort_by, sort_by)

    result = f"🏆 **基金排名（{category_str}，按{sort_str}排序，前{limit}名）**\n\n"

    for i, fund in enumerate(rankings, 1):
        result += f"{i}. **{fund['name']} ({fund['code']})**\n"
        result += f" - 单位净值：{fund['nav']} | 近1年：{fund['return_1y']}% | 近3年：{fund['return_3y']}%\n"

    return result


@tool
def get_fund_holdings(fund_code: str, period: str = "Q1") -> str:
    """查询基金持仓（重仓股、行业分布）

    Args:
        fund_code: 基金代码，例如 "000001", "005827"
        period: 报告期（"Q1": 一季报, "Q2": 二季报, "Q3": 三季报, "Q4": 四季报）

    Returns:
        基金持仓信息（前十大重仓股 + 行业分布）
    """
    holdings: FundHoldings = fund_data_service.get_fund_holdings(fund_code, period)

    if not holdings:
        return f"❌ 未找到基金代码 {fund_code} 的持仓数据"

    # 格式化输出：前十大重仓股
    result = f"📊 **{fund_code} 持仓信息（{period}）**\n\n"
    result += "**前十大重仓股**：\n"

    for i, holding in enumerate(holdings.top_holdings, 1):
        result += f"{i}. {holding.stock_name} ({holding.stock_code}) - 占比 {holding.weight}%\n"

    # 格式化输出：行业分布
    result += "\n**行业分布**：\n"
    for industry, weight in holdings.industry_distribution.items():
        result += f"- {industry}：{weight}%\n"

    return result


@tool
def get_fund_manager_info(fund_code: str) -> str:
    """查询基金经理信息（业绩、风格、管理规模）

    Args:
        fund_code: 基金代码，例如 "000001", "005827"

    Returns:
        基金经理的详细信息
    """
    fund_info: FundInfo = fund_data_service.get_fund_info(fund_code)

    if not fund_info:
        return f"❌ 未找到基金代码 {fund_code} 的信息"

    manager: FundManager = fund_info.manager

    # 格式化输出
    result = f"👨‍💼 **基金经理：{manager.name}**\n\n"
    result += f"**基本信息**：\n"
    result += f"- 从业年限：{manager.tenure_years} 年\n"
    result += f"- 投资风格：{manager.investment_style}\n"
    result += f"- 代表产品：{fund_info.name} ({fund_info.code})\n"

    return result


@tool
def search_funds(keyword: str, fund_type: str = None) -> str:
    """模糊搜索基金（名称、代码、类型筛选）

    Args:
        keyword: 搜索关键词（基金名称、代码、基金经理）
        fund_type: 基金类型筛选（"股票型", "混合型", "债券型"，留空表示不限）

    Returns:
        搜索结果列表
    """
    results = fund_data_service.search_funds(keyword)

    if not results:
        return f"❌ 未找到包含 '{keyword}' 的基金"

    # 按类型筛选
    if fund_type:
        results = [r for r in results if r.type == fund_type]

    if not results:
        return f"❌ 未找到类型为 '{fund_type}' 且包含 '{keyword}' 的基金"

    # 格式化输出
    result = f"🔍 **搜索结果：'{keyword}'（共 {len(results)} 只）**\n\n"

    for fund in results:
        result += f"✅ {fund.name} ({fund.code})\n"
        result += (
            f" - 类型：{fund.type} | 风险：{fund.risk_level} | 净值：{fund.nav.nav}\n"
        )

    return result

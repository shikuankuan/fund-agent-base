# app/tools/fund_info.py
from langchain_core.tools import tool
from services import fund_data_service


@tool
def get_fund_info(fund_code: str) -> str:
    """获取基金完整信息。

    Args:
    fund_code: 基金代码，例如 "000001"、"005827"

    Returns:
    基金的详细信息（名称、类型、风险等级、基金经理、净值等）
    """
    fund_info = fund_data_service.get_fund_info(fund_code)

    if not fund_info:
        return f"❌ 未找到基金代码 {fund_code} 的信息"

    # 格式化输出
    result = f"""📊 **{fund_info.name} ({fund_info.code})**

**基本信息**：
- 基金类型：{fund_info.type}
- 风险等级：{fund_info.risk_level}
- 基金公司：{fund_info.company}
- 基金规模：{fund_info.scale}
- 成立日期：{fund_info.establish_date}

**基金经理**：{fund_info.manager.name}
- 任职年限：{fund_info.manager.tenure_years} 年
- 投资风格：{fund_info.manager.investment_style}
- 历史业绩：1年 {fund_info.manager.historical_returns.get('1y', 'N/A')}%，3年 {fund_info.manager.historical_returns.get('3y', 'N/A')}%，5年 {fund_info.manager.historical_returns.get('5y', 'N/A')}%

**最新净值**（{fund_info.nav.nav_date}）：
- 单位净值：{fund_info.nav.nav}
- 累计净值：{fund_info.nav.accumulative_nav}
- 日涨跌幅：{fund_info.nav.daily_change}%
- 近一年涨幅：{fund_info.nav.yearly_change}%

**基金简介**：
{fund_info.description}
"""
    return result


@tool
def search_funds(keyword: str) -> str:
    """搜索基金（按名称或代码关键词）。

    Args:
    keyword: 搜索关键词，例如 "易方达"、"蓝筹"、"000001"

    Returns:
    匹配的基金列表
    """
    results = fund_data_service.search_funds(keyword)

    if not results:
        return f"❌ 未找到包含 '{keyword}' 的基金"

    fund_list = "\n".join([f"- {fund.name} ({fund.code})" for fund in results])
    return f"✅ 找到 {len(results)} 只基金：\n{fund_list}"


@tool
def get_fund_nav(fund_code: str) -> str:
    """获取基金净值信息。

    Args:
    fund_code: 基金代码，例如 "005827"

    Returns:
    基金的净值信息（单位净值、累计净值、涨跌幅等）
    """
    nav = fund_data_service.get_fund_nav(fund_code)

    if not nav:
        return f"❌ 未找到基金代码 {fund_code} 的净值信息"

    result = f"""📈 **{fund_code} 净值信息**（{nav.nav_date}）

- 单位净值：{nav.nav}
- 累计净值：{nav.accumulative_nav}
- 日涨跌幅：{nav.daily_change}%
- 近一周涨幅：{nav.weekly_change}%
- 近一月涨幅：{nav.monthly_change}%
- 近一年涨幅：{nav.yearly_change}%
"""
    return result


@tool
def get_fund_manager_info(fund_code: str) -> str:
    """获取基金经理信息。

    Args:
    fund_code: 基金代码，例如 "005827"

    Returns:
    基金经理的详细信息（姓名、任职年限、投资风格、历史业绩等）
    """
    manager = fund_data_service.get_fund_manager(fund_code)

    if not manager:
        return f"❌ 未找到基金代码 {fund_code} 的基金经理信息"

    result = f"""👨💼 **基金经理：{manager.name}**

- 任职年限：{manager.tenure_years} 年
- 当前管理基金：{', '.join(manager.current_funds)}
- 投资风格：{manager.investment_style}

**历史业绩**：
- 近1年：{manager.historical_returns.get('1y', 'N/A')}%
- 近3年：{manager.historical_returns.get('3y', 'N/A')}%
- 近5年：{manager.historical_returns.get('5y', 'N/A')}%
"""
    return result

# app/models/fund_models.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class FundManager(BaseModel):
    """基金经理信息"""

    name: str = Field(description="基金经理姓名")
    tenure_years: float = Field(description="任职年限")
    current_funds: List[str] = Field(description="当前管理基金列表")
    historical_returns: dict = Field(description="历史业绩")
    investment_style: str = Field(description="投资风格描述")


class FundNAV(BaseModel):
    """基金净值信息"""

    nav_date: date = Field(description="净值日期")
    nav: float = Field(description="单位净值")
    accumulative_nav: float = Field(description="累计净值")
    daily_change: float = Field(description="日涨跌幅(%)")
    weekly_change: float = Field(description="近一周涨幅(%)")
    monthly_change: float = Field(description="近一月涨幅(%)")
    yearly_change: float = Field(description="近一年涨幅(%)")


class FundHolding(BaseModel):
    """基金持仓信息"""

    rank: int = Field(description="持仓排名")
    stock_code: str = Field(description="股票代码")
    stock_name: str = Field(description="股票名称")
    shares: float = Field(description="持股数量")
    market_value: float = Field(description="持仓市值(万元)")
    proportion: float = Field(description="占净值比例(%)")


class FundHoldings(BaseModel):
    """基金持仓详情"""

    report_date: date = Field(description="报告期")
    top_holdings: List[FundHolding] = Field(description="前十大重仓股")
    industry_distribution: dict = Field(description="行业分布")
    asset_allocation: dict = Field(description="资产配置比例")


class FundRiskMetrics(BaseModel):
    """基金风险指标"""

    sharpe_ratio: float = Field(description="夏普比率")
    max_drawdown: float = Field(description="最大回撤(%)")
    volatility: float = Field(description="波动率(%)")
    beta: float = Field(description="Beta值")
    alpha: float = Field(description="Alpha值")


class FundInfo(BaseModel):
    """基金完整信息"""

    code: str = Field(description="基金代码")
    name: str = Field(description="基金名称")
    type: str = Field(description="基金类型")
    risk_level: str = Field(description="风险等级")
    manager: FundManager = Field(description="基金经理信息")
    company: str = Field(description="基金公司")
    nav: FundNAV = Field(description="净值信息")
    holdings: Optional[FundHoldings] = Field(default=None, description="持仓信息")
    risk_metrics: Optional[FundRiskMetrics] = Field(
        default=None, description="风险指标"
    )
    description: str = Field(description="基金简介")
    scale: str = Field(description="基金规模")
    founded_date: date = Field(description="成立日期")

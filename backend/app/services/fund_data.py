# app/services/fund_data.py
from datetime import date, timedelta
from typing import Optional, List, Dict
from app.models import (
    FundInfo,
    FundManager,
    FundNAV,
    FundHoldings,
    FundHolding,
    FundRiskMetrics,
)

# ============================================================
# 模拟数据（实际项目中从天天基金/东方财富/Tushare 获取）
# ============================================================

FUND_DATABASE: dict = {
    "000001": {
        "code": "000001",
        "name": "宽宽成长混合",
        "type": "混合型",
        "risk_level": "中风险",
        "founded_date": date(2018, 9, 5),
        "custodian": "中国银行",
        "manager": {
            "name": "王明",
            "tenure_years": 5.2,
            "current_funds": ["000001", "000002"],
            "historical_returns": {"1y": 15.2, "3y": 45.8, "5y": 82.3},
            "investment_style": "成长风格，注重选股",
        },
        "company": "宽宽基金",
        "nav": {
            "nav_date": date.today(),
            "nav": 1.2345,
            "accumulative_nav": 3.4567,
            "daily_change": 2.34,
            "weekly_change": 3.21,
            "monthly_change": 5.67,
            "yearly_change": 15.23,
        },
        "holdings": {
            "report_date": date(2024, 12, 31),
            "top_holdings": [
                {
                    "rank": 1,
                    "stock_code": "600519",
                    "stock_name": "贵州茅台",
                    "shares": 50.2,
                    "market_value": 9850.0,
                    "proportion": 8.5,
                },
                {
                    "rank": 2,
                    "stock_code": "000858",
                    "stock_name": "五粮液",
                    "shares": 120.5,
                    "market_value": 2340.0,
                    "proportion": 6.2,
                },
                {
                    "rank": 3,
                    "stock_code": "601318",
                    "stock_name": "中国平安",
                    "shares": 80.0,
                    "market_value": 1680.0,
                    "proportion": 5.8,
                },
            ],
            "industry_distribution": {
                "食品饮料": 25.5,
                "金融": 20.3,
                "医药": 15.2,
                "科技": 18.5,
            },
            "asset_allocation": {"股票": 78.5, "债券": 15.2, "现金": 6.3},
        },
        "risk_metrics": {
            "sharpe_ratio": 1.25,
            "max_drawdown": -18.5,
            "volatility": 15.2,
            "beta": 0.85,
            "alpha": 3.2,
        },
        "description": "华夏成长混合是一只混合型基金，主要投资于成长型股票，追求长期资本增值。",
        "scale": "50.2亿",
        "establish_date": date(2001, 12, 18),
    },
    "005827": {
        "code": "005827",
        "name": "易方达蓝筹精选混合",
        "type": "混合型",
        "risk_level": "中高风险",
        "founded_date": date(2018, 9, 5),
        "custodian": "中国银行",
        "manager": {
            "name": "张坤",
            "tenure_years": 8.5,
            "current_funds": ["005827", "110011"],
            "historical_returns": {"1y": 22.5, "3y": 85.3, "5y": 156.8},
            "investment_style": "价值成长风格，注重商业模式和竞争壁垒",
        },
        "company": "易方达基金",
        "nav": {
            "nav_date": date.today(),
            "nav": 2.3456,
            "accumulative_nav": 3.5678,
            "daily_change": 1.56,
            "weekly_change": 4.23,
            "monthly_change": 8.45,
            "yearly_change": 22.5,
        },
        "holdings": {
            "report_date": date(2024, 12, 31),
            "top_holdings": [
                {
                    "rank": 1,
                    "stock_code": "600519",
                    "stock_name": "贵州茅台",
                    "shares": 280.0,
                    "market_value": 54860.0,
                    "proportion": 9.8,
                },
                {
                    "rank": 2,
                    "stock_code": "000858",
                    "stock_name": "五粮液",
                    "shares": 650.0,
                    "market_value": 12612.0,
                    "proportion": 8.5,
                },
                {
                    "rank": 3,
                    "stock_code": "601318",
                    "stock_name": "中国平安",
                    "shares": 520.0,
                    "market_value": 10920.0,
                    "proportion": 7.2,
                },
                {
                    "rank": 4,
                    "stock_code": "600036",
                    "stock_name": "招商银行",
                    "shares": 480.0,
                    "market_value": 8640.0,
                    "proportion": 6.8,
                },
                {
                    "rank": 5,
                    "stock_code": "002415",
                    "stock_name": "海康威视",
                    "shares": 350.0,
                    "market_value": 7350.0,
                    "proportion": 5.6,
                },
            ],
            "industry_distribution": {
                "食品饮料": 28.5,
                "金融": 25.2,
                "医药": 12.3,
                "科技": 18.5,
            },
            "asset_allocation": {"股票": 85.2, "债券": 8.5, "现金": 6.3},
        },
        "risk_metrics": {
            "sharpe_ratio": 1.85,
            "max_drawdown": -22.3,
            "volatility": 18.5,
            "beta": 0.92,
            "alpha": 5.8,
        },
        "description": "易方达蓝筹精选混合主要投资于大盘蓝筹股，由明星基金经理张坤管理，坚持价值投资理念。",
        "scale": "280.5亿",
        "establish_date": date(2018, 9, 5),
    },
    "110011": {
        "code": "110011",
        "name": "易方达中小盘混合",
        "type": "混合型",
        "risk_level": "中高风险",
        "founded_date": date(2018, 9, 5),
        "custodian": "中国银行",
        "manager": {
            "name": "张坤",
            "tenure_years": 8.5,
            "current_funds": ["005827", "110011"],
            "historical_returns": {"1y": 18.5, "3y": 72.3, "5y": 125.6},
            "investment_style": "成长风格，注重企业竞争力",
        },
        "company": "易方达基金",
        "nav": {
            "nav_date": date.today(),
            "nav": 4.5678,
            "accumulative_nav": 5.8901,
            "daily_change": 3.21,
            "weekly_change": 5.12,
            "monthly_change": 9.85,
            "yearly_change": 18.5,
        },
        "holdings": {
            "report_date": date(2024, 12, 31),
            "top_holdings": [
                {
                    "rank": 1,
                    "stock_code": "300015",
                    "stock_name": "爱尔眼科",
                    "shares": 850.0,
                    "market_value": 21250.0,
                    "proportion": 9.5,
                },
                {
                    "rank": 2,
                    "stock_code": "300760",
                    "stock_name": "迈瑞医疗",
                    "shares": 120.0,
                    "market_value": 15600.0,
                    "proportion": 8.2,
                },
                {
                    "rank": 3,
                    "stock_code": "002821",
                    "stock_name": "凯莱英",
                    "shares": 95.0,
                    "market_value": 12350.0,
                    "proportion": 7.8,
                },
            ],
            "industry_distribution": {"医药": 45.2, "消费": 25.3, "科技": 15.5},
            "asset_allocation": {"股票": 88.5, "债券": 5.2, "现金": 6.3},
        },
        "risk_metrics": {
            "sharpe_ratio": 1.65,
            "max_drawdown": -25.8,
            "volatility": 22.3,
            "beta": 1.05,
            "alpha": 4.5,
        },
        "description": "易方达中小盘混合主要投资于中小盘成长股，追求长期资本增值。",
        "scale": "120.5亿",
        "establish_date": date(2012, 9, 28),
    },
    "000002": {
        "code": "000002",
        "name": "宽宽债券A",
        "type": "债券型",
        "risk_level": "中低风险",
        "founded_date": date(2015, 3, 12),
        "custodian": "工商银行",
        "manager": {
            "name": "王明",
            "tenure_years": 5.2,
            "current_funds": ["000001", "000002"],
            "historical_returns": {"1y": 4.5, "3y": 14.2, "5y": 28.6},
            "investment_style": "稳健风格，注重票息和久期管理",
        },
        "company": "宽宽基金",
        "nav": {
            "nav_date": date.today(),
            "nav": 1.1234,
            "accumulative_nav": 1.5678,
            "daily_change": 0.05,
            "weekly_change": 0.15,
            "monthly_change": 0.45,
            "yearly_change": 4.5,
        },
        "holdings": {
            "report_date": date(2024, 12, 31),
            "top_holdings": [
                {"rank": 1, "stock_code": "019706", "stock_name": "23国债06", "shares": 500.0, "market_value": 50250.0, "proportion": 4.2},
                {"rank": 2, "stock_code": "019704", "stock_name": "23国债04", "shares": 400.0, "market_value": 40200.0, "proportion": 3.5},
            ],
            "industry_distribution": {"国债": 35.0, "信用债": 45.0, "现金": 20.0},
            "asset_allocation": {"债券": 95.2, "现金": 4.8},
        },
        "risk_metrics": {
            "sharpe_ratio": 1.8,
            "max_drawdown": -1.2,
            "volatility": 1.5,
            "beta": 0.05,
            "alpha": 0.3,
        },
        "description": "宽宽债券A是一只纯债基金，主要投资信用债和利率债，追求稳健收益。",
        "scale": "120亿",
        "establish_date": date(2015, 3, 12),
    },
    "510300": {
        "code": "510300",
        "name": "沪深300ETF",
        "type": "股票型",
        "risk_level": "中风险",
        "founded_date": date(2012, 5, 4),
        "custodian": "工商银行",
        "manager": {
            "name": "李明",
            "tenure_years": 6.8,
            "current_funds": ["510300"],
            "historical_returns": {"1y": 8.5, "3y": 25.3, "5y": 42.6},
            "investment_style": "被动指数投资，紧密跟踪沪深300",
        },
        "company": "华泰柏瑞基金",
        "nav": {
            "nav_date": date.today(),
            "nav": 3.4567,
            "accumulative_nav": 4.5678,
            "daily_change": 0.85,
            "weekly_change": 2.15,
            "monthly_change": 3.67,
            "yearly_change": 8.5,
        },
        "holdings": {
            "report_date": date(2024, 12, 31),
            "top_holdings": [
                {"rank": 1, "stock_code": "600519", "stock_name": "贵州茅台", "shares": 300.0, "market_value": 58800.0, "proportion": 6.2},
                {"rank": 2, "stock_code": "601318", "stock_name": "中国平安", "shares": 580.0, "market_value": 12180.0, "proportion": 3.8},
                {"rank": 3, "stock_code": "600036", "stock_name": "招商银行", "shares": 450.0, "market_value": 8100.0, "proportion": 3.2},
            ],
            "industry_distribution": {"金融": 28.5, "食品饮料": 18.3, "医药": 12.5, "科技": 15.2},
            "asset_allocation": {"股票": 98.5, "现金": 1.5},
        },
        "risk_metrics": {
            "sharpe_ratio": 0.65,
            "max_drawdown": -28.5,
            "volatility": 20.5,
            "beta": 1.0,
            "alpha": -0.2,
        },
        "description": "沪深300ETF是被动指数基金，跟踪沪深300指数，代表大盘蓝筹。",
        "scale": "380亿",
        "establish_date": date(2012, 5, 4),
    },
}

# ============================================================
# 数据服务类
# ============================================================


class FundDataService:
    """基金数据服务类（统一数据访问接口）"""

    def __init__(self):
        """初始化数据服务"""
        self._cache = {}  # 简单内存缓存
        self._cache_ttl = 300  # 缓存5分钟（实际项目中可用Redis）

    def get_fund_info(self, fund_code: str) -> Optional[FundInfo]:
        """获取基金完整信息

        Args:
            fund_code: 基金代码，如 "005827"

        Returns:
            FundInfo: 基金信息，未找到返回 None
        """
        fund_data = FUND_DATABASE.get(fund_code)
        if not fund_data:
            return None

        # 转换为 Pydantic 模型
        return FundInfo(**fund_data)

    def get_fund_nav(self, fund_code: str) -> Optional[FundNAV]:
        """获取基金净值信息"""
        fund_info = self.get_fund_info(fund_code)
        return fund_info.nav if fund_info else None

    def get_fund_holdings(self, fund_code: str) -> Optional[FundHoldings]:
        """获取基金持仓信息"""
        fund_info = self.get_fund_info(fund_code)
        return fund_info.holdings if fund_info else None

    def get_fund_manager(self, fund_code: str) -> Optional[FundManager]:
        """获取基金经理信息"""
        fund_info = self.get_fund_info(fund_code)
        return fund_info.manager if fund_info else None

    def get_fund_risk_metrics(self, fund_code: str) -> Optional[FundRiskMetrics]:
        """获取基金风险指标"""
        fund_info = self.get_fund_info(fund_code)
        return fund_info.risk_metrics if fund_info else None

    def search_funds(self, keyword: str) -> List[FundInfo]:
        """搜索基金（按名称或代码）

        Args:
            keyword: 搜索关键词

        Returns:
            List[FundInfo]: 匹配的基金列表
        """
        results = []
        for fund_data in FUND_DATABASE.values():
            if (
                keyword.lower() in fund_data["code"].lower()
                or keyword.lower() in fund_data["name"].lower()
            ):
                results.append(FundInfo(**fund_data))
        return results

    def get_funds_by_type(self, fund_type: str) -> List[FundInfo]:
        """按类型筛选基金"""
        results = []
        for fund_data in FUND_DATABASE.values():
            if fund_type in fund_data["type"]:
                results.append(FundInfo(**fund_data))
        return results

    def get_fund_ranking(
        self, category: str = None, sort_by: str = "nav", limit: int = 10
    ) -> List[dict]:
        """获取基金排名

        Args:
            category: 基金类型（"股票型", "混合型", "债券型", None表示全部）
            sort_by: 排序字段（"nav", "return_1y", "return_3y"）
            limit: 返回数量

        Returns:
            排名列表
        """
        # Mock 排名数据
        rankings = [
            {
                "code": "000001",
                "name": "华夏成长混合",
                "nav": 1.2345,
                "return_1y": 15.6,
                "return_3y": 45.2,
                "category": "混合型",
            },
            {
                "code": "005827",
                "name": "易方达蓝筹精选混合",
                "nav": 2.3456,
                "return_1y": 15.6,
                "return_3y": 45.2,
                "category": "混合型",
            },
            {
                "code": "110011",
                "name": "易方达中小盘混合",
                "nav": 4.5678,
                "return_1y": 12.3,
                "return_3y": 38.7,
                "category": "混合型",
            },
            {
                "code": "000002",
                "name": "华夏债券A",
                "nav": 1.1234,
                "return_1y": 5.6,
                "return_3y": 18.9,
                "category": "债券型",
            },
            {
                "code": "510300",
                "name": "华泰柏瑞沪深300ETF",
                "nav": 3.4567,
                "return_1y": 8.9,
                "return_3y": 25.4,
                "category": "股票型",
            },
        ]

        # 按类别筛选
        if category:
            rankings = [r for r in rankings if r["category"] == category]

        # 排序
        reverse = True  # 降序
        if sort_by == "nav":
            rankings.sort(key=lambda x: x["nav"], reverse=reverse)
        elif sort_by == "return_1y":
            rankings.sort(key=lambda x: x["return_1y"], reverse=reverse)
        elif sort_by == "return_3y":
            rankings.sort(key=lambda x: x["return_3y"], reverse=reverse)

        return rankings[:limit]

    def get_fund_holdings(
        self, fund_code: str, period: str = "Q1"
    ) -> Optional[FundHoldings]:
        """获取基金持仓

        Args:
            fund_code: 基金代码
            period: 报告期（"Q1", "Q2", "Q3", "Q4"）

        Returns:
            持仓信息
        """
        # Mock 持仓数据
        holdings_data = {
            "000001": FundHoldings(
                fund_code="000001",
                period=period,
                top_holdings=[
                    FundHolding(stock_code="600519", stock_name="贵州茅台", weight=8.5),
                    FundHolding(stock_code="000858", stock_name="五粮液", weight=6.2),
                    FundHolding(stock_code="601318", stock_name="中国平安", weight=5.8),
                ],
                industry_distribution={
                    "食品饮料": 25.6,
                    "金融": 18.3,
                    "医药生物": 15.2,
                    "电子": 12.4,
                    "其他": 28.5,
                },
            ),
            "005827": FundHoldings(
                fund_code="005827",
                period=period,
                top_holdings=[
                    FundHolding(stock_code="600519", stock_name="贵州茅台", weight=9.6),
                    FundHolding(stock_code="000568", stock_name="泸州老窖", weight=7.8),
                    FundHolding(stock_code="600809", stock_name="山西汾酒", weight=6.5),
                ],
                industry_distribution={
                    "食品饮料": 45.6,
                    "医药生物": 15.3,
                    "电子": 10.2,
                    "金融": 8.5,
                    "其他": 20.4,
                },
            ),
        }

        return holdings_data.get(fund_code)

    def get_fund_nav_history(
        self, fund_code: str, date_range: str = "1m"
    ) -> List[Dict]:
        """获取基金净值历史

        Args:
            fund_code: 基金代码
            date_range: 时间范围（"1w", "1m", "3m", "6m", "1y"）

        Returns:
            净值历史列表
        """
        import datetime as dt
        import random

        fund_data = FUND_DATABASE.get(fund_code)
        if not fund_data:
            return []

        # 用该基金真实当前净值作为基准
        base_nav = fund_data["nav"]["nav"]
        fund_type = fund_data["type"]

        # 不同类型基金波动率不同
        volatility_map = {
            "股票型": 2.5,
            "混合型": 1.8,
            "债券型": 0.3,
            "货币型": 0.05,
        }
        vol = volatility_map.get(fund_type, 1.5)

        # 不同类型基金的长期趋势（年化）
        trend_map = {
            "股票型": 8.0 / 365,
            "混合型": 6.0 / 365,
            "债券型": 3.5 / 365,
            "货币型": 2.0 / 365,
        }
        daily_trend = trend_map.get(fund_type, 5.0 / 365)

        days_map = {"1w": 7, "1m": 30, "3m": 90, "6m": 180, "1y": 365}
        days = days_map.get(date_range, 30)

        nav_history = []
        rand = random.Random(42 + int(fund_code) % 100)  # 固定种子，同基金同序列
        current = base_nav

        for i in range(days):
            d = dt.date.today() - dt.timedelta(days=days - i)
            if i == 0:
                # 第一天从远端起算：用随机游走倒退
                temp = base_nav
                for _ in range(days):
                    temp /= (1 + daily_trend + rand.gauss(0, vol / 100))
                current = round(temp, 4)

            # 每天波动 = 趋势 + 随机（正态分布）
            daily_return = daily_trend + rand.gauss(0, vol / 100)
            current = round(current * (1 + daily_return), 4)

            nav_history.append(
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "nav": current,
                    "change_pct": round(daily_return * 100, 2),
                }
            )

        return nav_history


# 创建全局数据服务实例
fund_data_service = FundDataService()

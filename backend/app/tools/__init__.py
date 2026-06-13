# app/tools/__init__.py

# 导入查询类工具
from app.tools.query_tools import (
    get_fund_info,
    get_fund_nav,
    get_fund_ranking,
    get_fund_holdings,
    get_fund_manager_info,
    search_funds,
)

# 导入分析类工具
from app.tools.analysis_tools import (
    compare_funds,
    calc_return,
    risk_analysis,
    portfolio_analysis,
)

# 导入合规类工具
from app.tools.compliance_tools import (
    check_risk_match,
    check_compliance,
    risk_disclosure,
)

# 导入 RAG 工具
from app.tools.rag_tools import rag_query

# 导出所有工具
__all__ = [
    # 查询类工具（6个）
    "get_fund_info",
    "get_fund_nav",
    "get_fund_ranking",
    "get_fund_holdings",
    "get_fund_manager_info",
    "search_funds",
    # 分析类工具（4个）
    "compare_funds",
    "calc_return",
    "risk_analysis",
    "portfolio_analysis",
    # 合规类工具（3个）
    "check_risk_match",
    "check_compliance",
    "risk_disclosure",
    # RAG 工具
    "rag_query",
]

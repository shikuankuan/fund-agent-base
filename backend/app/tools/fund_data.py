# backend/app/tools/fund_data.py

# Mock 基金数据集
FUND_DATABASE = {
    "000001": {
        "code": "000001",
        "name": "华夏成长混合",
        "type": "混合型",
        "manager": "王明",
        "company": "华夏基金",
        "nav": 1.2345,
        "growth_rate": "+2.34%",
        "establish_date": "2001-12-18",
        "scale": "50.2亿",
        "description": "华夏成长混合是一只混合型基金，主要投资于成长型股票。",
    },
    "000002": {
        "code": "000002",
        "name": "南方稳健成长",
        "type": "股票型",
        "manager": "李明",
        "company": "南方基金",
        "nav": 2.3456,
        "growth_rate": "+1.56%",
        "establish_date": "2002-05-20",
        "scale": "30.8亿",
        "description": "南方稳健成长是一只股票型基金，追求长期稳健增长。",
    },
    "110011": {
        "code": "110011",
        "name": "易方达中小盘混合",
        "type": "混合型",
        "manager": "张坤",
        "company": "易方达基金",
        "nav": 4.5678,
        "growth_rate": "+3.21%",
        "establish_date": "2012-09-28",
        "scale": "120.5亿",
        "description": "易方达中小盘混合主要投资于中小盘股票，由知名基金经理张坤管理。",
    },
}

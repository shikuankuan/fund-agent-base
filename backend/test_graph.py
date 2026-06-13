"""测试状态图"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent.graph import fund_agent_graph
from langchain_core.messages import HumanMessage


def test_graph():
    """测试状态图执行"""

    # ========== 测试 1: 分析基金风险（完整流程） ==========
    print("=" * 60)
    print("测试 1: 分析 005827 的风险 + R3 合规检查")
    print("=" * 60)

    result = fund_agent_graph.invoke(
        {
            "messages": [
                HumanMessage(content="分析 005827 的风险，检查是否适合 R3 投资者")
            ],
            "user_intent": None,
            "current_fund": None,
            "analysis_result": None,
            "compliance_result": None,
            "final_response": None,
        }
    )

    print("\n[测试 1 结果]")
    print(f"  用户意图: {result.get('user_intent')}")
    print(f"  当前基金: {result.get('current_fund')}")
    print(f"  分析结果: {result.get('analysis_result')}")
    print(f"  合规结果: {result.get('compliance_result')}")
    print(f"  最终回复: {result.get('final_response')[:150]}...")

    # ========== 测试 2: 查询基金（简单流程） ==========
    print("\n" + "=" * 60)
    print("测试 2: 查询 000001 基金信息")
    print("=" * 60)

    result2 = fund_agent_graph.invoke(
        {
            "messages": [HumanMessage(content="000001 这只基金怎么样？")],
            "user_intent": None,
            "current_fund": None,
            "analysis_result": None,
            "compliance_result": None,
            "final_response": None,
        }
    )

    print("\n[测试 2 结果]")
    print(f"  用户意图: {result2.get('user_intent')}")
    print(f"  当前基金: {result2.get('current_fund')}")
    print(f"  最终回复: {result2.get('final_response')[:150]}...")

    print("\n" + "=" * 60)
    print("所有测试通过！✅")
    print("=" * 60)


if __name__ == "__main__":
    test_graph()

"""可视化状态图"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent.graph import fund_agent_graph


def visualize():
    """生成状态图可视化"""

    # ========== 1. ASCII 图（终端显示） ==========
    print("=" * 60)
    print("ASCII 状态图")
    print("=" * 60)
    graph = fund_agent_graph.get_graph()
    graph.print_ascii()

    print()

    # ========== 2. Mermaid 图（Markdown 格式） ==========
    print("=" * 60)
    print("Mermaid 状态图（可粘贴到 Markdown 编辑器渲染）")
    print("=" * 60)
    mermaid_code = graph.draw_mermaid()
    print(mermaid_code)

    print()

    # ========== 3. 节点和边统计 ==========
    print("=" * 60)
    print("状态图统计")
    print("=" * 60)
    print(f"节点数量: {len(graph.nodes)}")
    print(f"边数量: {len(graph.edges)}")
    print(f"节点列表: {list(graph.nodes.keys())}")

    # 统计条件边和固定边
    conditional_count = 0
    fixed_count = 0
    for edge in graph.edges:
        if edge.conditional:
            conditional_count += 1
        else:
            fixed_count += 1
    print(f"固定边: {fixed_count}, 条件边: {conditional_count}")


if __name__ == "__main__":
    visualize()

"""
测试多轮对话（Checkpointer 集成后）
验证 Agent 是否记住了上下文
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"
SESSION_ID = "test-multi-turn-001"


def chat(message: str) -> dict:
    response = requests.post(
        f"{BASE_URL}/chat", json={"message": message, "session_id": SESSION_ID}
    )
    return response.json()


print("=" * 60)
print("测试多轮对话（Checkpointer）")
print(f"会话 ID: {SESSION_ID}")
print("=" * 60)

# 第 1 轮：查询基金
print("\n" + "=" * 60)
print("【第 1 轮】")
print("=" * 60)
response1 = chat("000001 基金怎么样？")
print(f"用户: 000001 基金怎么样？")
print(f"Agent: {response1.get('reply', '')}")

# 第 2 轮：追问（没有指定基金代码）
print("\n" + "=" * 60)
print("【第 2 轮】")
print("=" * 60)
response2 = chat("005827 基金和它比呢？")
print(f"用户: 005827 基金和它比呢？")
print(f"Agent: {response2.get('reply', '')}")

# 第 2 轮：追问（没有指定基金代码）
print("\n" + "=" * 60)
print("【第 3 轮】")
print("=" * 60)
response2 = chat("它的基金经理是谁？")
print(f"用户: 它的基金经理是谁？")
print(f"Agent: {response2.get('reply', '')}")

# 第 3 轮：对比（没有重新指定基金代码）
print("\n" + "=" * 60)
print("【第 4 轮】")
print("=" * 60)
response3 = chat("他管的另一只呢？")
print(f"用户: 他管的另一只呢？")
print(f"Agent: {response3.get('reply', '')}")

# ========== 验证点 ==========

print("\n" + "=" * 60)
print("验证结果")
print("=" * 60)

reply2 = response2.get("reply", "")
reply3 = response3.get("reply", "")
if "005827" in reply2 and "000001" in reply2:
    print("✅ 第 2 轮追问正确识别了两只基金")
else:
    print("❌ 第 2 轮追问没有正确识别两只基金")

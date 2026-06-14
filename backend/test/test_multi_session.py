"""验证多用户会话隔离"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def chat(session_id: str, message: str, label: str = ""):
    """发送聊天请求并打印结果"""
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"message": message, "session_id": session_id},
    )
    data = resp.json()
    reply = data.get("reply", "无回复")
    print(f"[{label or session_id}] {message}")
    print(f"  → {reply[:120]}...")
    print()
    return reply


print("=" * 60)
print("多用户会话隔离测试")
print("=" * 60)

# ===== 用户 A：新手投资者 =====
print("\n--- 用户 A：我是R2保守型，刚入门 ---\n")
chat("user_a", "我是R2风险等级的投资者，000001这只基金适合我吗？", "A")

# ===== 用户 B：老手投资者 =====
print("\n--- 用户 B：我是R5激进型，追求高收益 ---\n")
chat("user_b", "我是R5风险等级的投资者，想看005827的详细分析", "B")

# ===== 用户 A 继续追问（验证隔离） =====
print("\n--- 用户 A 追问 ---\n")
chat("user_a", "那我适合买什么类型的基金？", "A")

# ===== 用户 B 继续追问（验证隔离） =====
print("\n--- 用户 B 追问 ---\n")
chat("user_b", "它的基金经理管理能力怎么样？", "B")

print("=" * 60)
print("验证要点：")
print("1. 用户A的回答应基于R2风险等级，不涉及005827")
print("2. 用户B的回答应基于R5风险等级，能理解'它'=005827")
print("3. 两个用户的对话完全独立")
print("=" * 60)

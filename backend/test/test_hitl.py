"""Day 9 HITL 全流程模拟测试

测试 3 个场景：
  场景A: 含敏感词 → block → 驳回
  场景B: 含敏感词 → block → 强制放行
  场景C: 无敏感词 → 正常通过

运行前确保服务已启动：
  cd /Users/skk/Documents/code/fund-agent-base/backend
  conda run -n fund-agent python -m uvicorn app.main:app --reload
"""

import requests
import json

BASE = "http://localhost:8000/api"

# ============================================================
# 场景 A：含敏感词 → block → 驳回
# ============================================================

print("=" * 60)
print("场景 A：含敏感词 → block → 驳回")
print("=" * 60)

session_a = "hitl-test-a"

# 1. 发送含敏感词的消息
resp = requests.post(
    f"{BASE}/chat",
    json={
        "message": "你帮我看看000001这个基金，是不是guaranteed收益，稳赚不赔的？",
        "session_id": session_a,
    },
)
print(f"1. /chat 返回: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")

data = resp.json()
assert data["status"] == "interrupted", f"期望 interrupted，实际 {data['status']}"
assert (
    data["compliance_result"]["grade"] == "block"
), f"期望 block，实际 {data['compliance_result']['grade']}"

# 2. 查看审查详情
checks = data["compliance_result"]["checks"]
for c in checks:
    if not c["passed"]:
        print(f"   ❌ {c['name']}: {c['detail']}")

# 3. 驳回
resp = requests.post(
    f"{BASE}/approval",
    json={
        "session_id": session_a,
        "action": "reject",
    },
)
print(f"\n3. /approval (reject) 返回:")
print(f"   {resp.json()['reply'][:200]}...")

# 4. 验证驳回回复
assert "合规审查未通过" in resp.json()["reply"], "驳回回复应包含拦截提示"
print("\n✅ 场景 A 通过：含敏感词 → block → 驳回 → 拦截提示")

# ============================================================
# 场景 B：含敏感词 → block → 强制放行
# ============================================================

print("\n" + "=" * 60)
print("场景 B：含敏感词 → block → 强制放行")
print("=" * 60)

session_b = "hitl-test-b"

# 1. 发送含敏感词的消息
resp = requests.post(
    f"{BASE}/chat",
    json={
        "message": "000001这个基金确定收益吗？我是R3投资者",
        "session_id": session_b,
    },
)
data = resp.json()
print(f"1. /chat 返回: status={data.get('status')}, keys={list(data.keys())}")
if data.get("status") == "interrupted":
    print(f"   grade={data['compliance_result']['grade']}")

assert (
    data.get("status") == "interrupted"
), f"期望interrupted，实际{data.get('status')}，keys={list(data.keys())}"
assert (
    data.get("compliance_result", {}).get("grade") == "block"
), f"grade={data.get('compliance_result', {}).get('grade')}"


# 2. 强制 approve（人工判断后放行）
resp = requests.post(
    f"{BASE}/approval",
    json={
        "session_id": session_b,
        "action": "approve",
    },
)
print(f"2. /approval (approve) 返回:")
print(f"   {resp.json()['reply'][:200]}...")

# 3. 验证：放行后 LLM 应生成完整回复
assert resp.json()["status"] == "resumed"
assert len(resp.json()["reply"]) > 20
print("\n✅ 场景 B 通过：含敏感词 → block → approve → 正常回复")

# ============================================================
# 场景 C：正常消息 → 不中断
# ============================================================

print("\n" + "=" * 60)
print("场景 C：正常消息 → 不中断（pass 级）")
print("=" * 60)

session_c = "hitl-test-c"

resp = requests.post(
    f"{BASE}/chat",
    json={
        "message": "帮我查一下000001的基本信息",
        "session_id": session_c,
    },
)
print(
    f"1. /chat 返回: status={resp.json().get('status')}, reply={resp.json()['reply'][:100]}..."
)

# 正常消息应直接完成，不返回 interrupted
assert (
    resp.json().get("status") != "interrupted"
), f"正常消息不应被中断，实际 status={resp.json().get('status')}"
print("\n✅ 场景 C 通过：正常消息 → pass → 无需审批")

# ============================================================
# 汇总
# ============================================================

print("\n" + "=" * 60)
print("🎉 全部 3 个场景测试通过！")
print("=" * 60)
print("  ✅ 场景 A: 敏感词 → block → reject → 拦截提示")
print("  ✅ 场景 B: 敏感词 → block → approve → 正常回复")
print("  ✅ 场景 C: 正常消息 → pass → 自动完成")

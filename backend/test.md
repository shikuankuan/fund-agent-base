# 测试 1：查询基金信息
curl -X POST "http://localhost:8000/api/chat" \
 -H "Content-Type: application/json" \
 -d '{"message": "000001这只基金怎么样？", "session_id": "test-001"}'

# 测试 2：搜索基金
curl -X POST "http://localhost:8000/api/chat" \
 -H "Content-Type: application/json" \
 -d '{"message": "搜索易方达的基金", "session_id": "test-001"}'

# 测试 3：查询净值
curl -X POST "http://localhost:8000/api/chat" \
 -H "Content-Type: application/json" \
 -d '{"message": "005827的净值是多少？", "session_id": "test-001"}'

# 测试 4：查询基金经理
curl -X POST "http://localhost:8000/api/chat" \
 -H "Content-Type: application/json" \
 -d '{"message": "005827的基金经理是谁？业绩如何？", "session_id": "test-001"}'


# 第一轮：查询基金
curl -X POST "http://localhost:8000/api/chat" \
 -H "Content-Type: application/json" \
 -d '{"message": "005827这只基金怎么样？", "session_id": "test-002"}'

# 第二轮：追问（应该使用同一 session_id）
curl -X POST "http://localhost:8000/api/chat" \
 -H "Content-Type: application/json" \
 -d '{"message": "它的基金经理是谁？", "session_id": "test-002"}'

# 第三轮：继续追问
curl -X POST "http://localhost:8000/api/chat" \
 -H "Content-Type: application/json" \
 -d '{"message": "他的投资风格是什么？", "session_id": "test-002"}'


curl -X POST "http://localhost:8000/api/chat" -H "Content-Type: application/json" -d '{
 "message": "我是 C3 型投资者，005827（R4）适合我吗？",
 "session_id": "test-compliance-001"
}'


# 向量检索
# 测试 1：知识库问题（应该调用 RAG 工具）
curl -X POST "http://localhost:8000/api/chat" \
 -H "Content-Type: application/json" \
 -d '{
 "message": "什么是基金？",
 "session_id": "test-session-001"
 }'

# 预期：Agent 调用 rag_query 工具，返回基于知识库的回答

# 测试 2：基金查询问题（应该调用 get_fund_info 工具）
curl -X POST "http://localhost:8000/api/chat" \
 -H "Content-Type: application/json" \
 -d '{
 "message": "000001 这只基金怎么样？",
 "session_id": "test-session-001"
 }'

# 预期：Agent 调用 get_fund_info、analyze_fund_performance、analyze_fund_risk 工具

# 测试 3：合规问题（应该调用 check_risk_match + rag_query）
curl -X POST "http://localhost:8000/api/chat" \
 -H "Content-Type: application/json" \
 -d '{
 "message": "我有 10 万，能买高风险基金吗？",
 "session_id": "test-session-001"
 }'

# 预期：Agent 调用 check_risk_match 和 rag_query 工具

# 测试langGraph调用
curl -X POST "http://127.0.0.1:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  --no-buffer \
  -d '{
    "message": "分析 005827 的风险，检查是否适合 R3 投资者",
    "session_id": "test-stream-001"
  }'

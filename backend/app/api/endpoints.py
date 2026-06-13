"""API 路由定义"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import json
import asyncio

from app.agent.graph import fund_agent_graph

# ========== 请求/响应模型 ==========


class ChatRequest(BaseModel):
    """聊天请求"""

    message: str
    session_id: Optional[str] = "default"
    history: Optional[List[dict]] = None


# ========== 路由定义 ==========

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    """非流式聊天接口（使用 LangGraph Agent）"""
    try:
        # 1. 构建初始状态
        from langchain_core.messages import HumanMessage

        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "user_intent": None,
            "current_fund": None,
            "analysis_result": None,
            "compliance_result": None,
            "final_response": None,
        }

        print(f"[LangGraph] 用户消息: {request.message}")

        # 2. 执行状态图
        result = fund_agent_graph.invoke(initial_state)

        print(f"[LangGraph] 执行完成")

        # 3. 提取最终回复
        final_response = result.get("final_response")
        if not final_response:
            messages = result.get("messages", [])
            if messages:
                final_response = messages[-1].content

        print(f"[LangGraph] 最终回复: {final_response[:100]}...")

        # 4. 返回响应
        return {"reply": final_response, "session_id": request.session_id}

    except Exception as e:
        print(f"[LangGraph] 错误: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口（真正的 SSE 流式输出）

    使用 LangGraph 的 astream_events() 实现真正的流式输出。
    监听 on_chat_model_stream 事件，逐 token 返回。

    Args:
        request: 聊天请求

    Returns:
        StreamingResponse: SSE 流式响应
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        """生成 SSE 事件流（真正的流式输出）

        Yields:
            SSE 格式的事件（data: {...}\n\n）
        """
        try:
            # 1. 构建初始状态
            from langchain_core.messages import HumanMessage

            initial_state = {
                "messages": [HumanMessage(content=request.message)],
                "user_intent": None,
                "current_fund": None,
                "analysis_result": None,
                "compliance_result": None,
                "final_response": None,
            }

            print(f"[LangGraph Stream] 用户消息: {request.message}")
            print(f"[LangGraph Stream] 开始流式输出...")

            # 2. 使用 astream_events() 监听事件
            # async for：异步迭代（每次生成一个事件）
            async for event in fund_agent_graph.astream_events(
                initial_state, version="v2"  # 使用 v2 版本（更详细）
            ):
                # 3. 只处理 LLM 生成 token 的事件
                if event["event"] == "on_chat_model_stream":
                    # 提取 token（chunk.content）
                    chunk = event["data"]["chunk"]
                    token = chunk.content

                    # 如果是空 token，跳过
                    if not token:
                        continue

                    # 4. 返回 SSE 事件（data: {"token": "..."}\n\n）
                    event_data = {"token": token}
                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                # 5. （可选）处理节点开始/结束事件（用于调试）
                elif event["event"] == "on_chain_start":
                    node_name = event["name"]
                    print(f"[LangGraph Stream] 节点开始: {node_name}")

                elif event["event"] == "on_chain_end":
                    node_name = event["name"]
                    print(f"[LangGraph Stream] 节点结束: {node_name}")

            # 6. 流式输出结束，发送 [DONE] 事件
            yield "data: [DONE]\n\n"

            print(f"[LangGraph Stream] 流式输出完成")

        except Exception as e:
            # 7. 错误处理
            error_msg = str(e)
            print(f"[LangGraph Stream] 错误: {error_msg}")
            import traceback

            traceback.print_exc()

            error_data = {"error": error_msg}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    # 8. 返回 StreamingResponse
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "agent": "LangGraph"}


@router.get("/agent/graph/mermaid")
async def get_graph_mermaid():
    """获取状态图的 Mermaid 代码（可直接渲染）"""
    graph = fund_agent_graph.get_graph()
    mermaid_code = graph.draw_mermaid()
    return {"mermaid": mermaid_code}


@router.get("/agent/graph/image")
async def get_graph_image():
    """获取状态图的 PNG 图片（base64 编码）"""
    import base64

    graph = fund_agent_graph.get_graph()
    image_bytes = graph.draw_mermaid_png()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    return {"image": f"data:image/png;base64,{image_b64}"}

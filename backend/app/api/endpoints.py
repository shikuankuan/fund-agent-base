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
        }

        print(f"[LangGraph] 用户消息: {request.message}")
        print(f"[LangGraph] 会话 ID: {request.session_id}")

        config = {"configurable": {"thread_id": request.session_id}}
        # 2. 执行状态图
        result = fund_agent_graph.invoke(initial_state, config=config)

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
    """流式聊天接口（SSE + Checkpointer 持久化）

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
            }

            print(f"\n{'='*60}")
            print(f"[LangGraph Stream] 用户消息: {request.message}")
            print(f"[LangGraph Stream] 会话 ID: {request.session_id}")

            # 2. 使用 astream_events() 监听事件
            # async for：异步迭代（每次生成一个事件）
            # 传入 config（含 thread_id），确保 Checkpointer 正确关联会话
            config = {"configurable": {"thread_id": request.session_id}}
            async for event in fund_agent_graph.astream_events(
                initial_state, config=config, version="v2"  # 使用 v2 版本（更详细）
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


# ========== 会话管理 ==========

import sqlite3
from datetime import datetime


@router.get("/sessions")
async def list_sessions():
    """列出所有活跃会话及其最后活动时间"""
    try:
        conn = sqlite3.connect(".langgraph.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT thread_id, 
                   MAX(json_extract(metadata, '$.step')) as last_step,
                   COUNT(*) as checkpoint_count
            FROM checkpoints 
            GROUP BY thread_id
            ORDER BY last_step DESC
        """)

        sessions = []
        for row in cursor.fetchall():
            thread_id, last_step, count = row
            sessions.append(
                {
                    "session_id": thread_id,
                    "last_step": last_step,
                    "checkpoint_count": count,
                }
            )

        conn.close()
        return {"total_sessions": len(sessions), "sessions": sessions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话的所有检查点"""
    try:
        conn = sqlite3.connect(".langgraph.db")
        cursor = conn.cursor()

        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (session_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return {
            "deleted": True,
            "session_id": session_id,
            "checkpoints_removed": deleted,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/cleanup")
async def cleanup_sessions(max_sessions: int = 50):
    """清理旧会话，保留最近的 N 个"""
    try:
        conn = sqlite3.connect(".langgraph.db")
        cursor = conn.cursor()

        # 找出需要删除的旧会话（按最后检查点排序）
        cursor.execute(
            """
            SELECT thread_id
            FROM checkpoints 
            GROUP BY thread_id
            ORDER BY MAX(checkpoint_id) DESC
            LIMIT -1 OFFSET ?
        """,
            (max_sessions,),
        )

        to_delete = [row[0] for row in cursor.fetchall()]

        if not to_delete:
            conn.close()
            return {"deleted_sessions": 0, "message": "无需清理"}

        placeholders = ",".join("?" * len(to_delete))
        cursor.execute(
            f"DELETE FROM checkpoints WHERE thread_id IN ({placeholders})",
            to_delete,
        )
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return {
            "deleted_sessions": len(to_delete),
            "checkpoints_removed": deleted_count,
            "sessions": to_delete,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

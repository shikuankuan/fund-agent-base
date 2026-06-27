"""API 路由定义"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import json

from app.agent.graph import get_graph
from app.services.fund_data import fund_data_service
from langgraph.errors import GraphInterrupt

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
        thread_id = request.session_id
        config = {"configurable": {"thread_id": thread_id}}
        # 2. 执行状态图
        try:

            result = await get_graph().ainvoke(initial_state, config=config)
            # 检查图是否被中断
            current = await get_graph().aget_state(config)
            pending = current.next  # 空列表 = 完成，非空 = 中断
            print(f"[LangGraph] 执行完成")

            if pending:
                # 图停在 compliance_checker 之后，等待审批
                compliance = current.values.get("compliance_result", {})
                return {
                    "reply": f"⏸️ 合规审查 [{compliance.get('grade')}]，等待审批",
                    "session_id": thread_id,
                    "status": "interrupted",
                    "compliance_result": compliance,
                    "pending_nodes": pending,
                }

            # 图正常跑完了
            return {
                "reply": result.get("final_response", "你好，有什么可以帮你的？"),
                "session_id": thread_id,
                "status": "completed",
            }
        except GraphInterrupt as gi:
            # 被中断了！当前状态已保存在 Checkpointer 里
            current_state = await get_graph().aget_state(config)
            compliance = current_state.values.get("compliance_result", {})

            return {
                "reply": f"⏸️ 合规审查完成，等待人工审批。\n审查结果：{compliance}",
                "session_id": request.session_id,
                "status": "interrupted",
                "compliance_result": compliance,  # ← 前端用它渲染审批界面
            }

    except Exception as e:
        print(f"[LangGraph] 错误: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口（SSE + Checkpointer 持久化 + 合规中断）

    使用 LangGraph 的 astream_events() 实现真正的流式输出。
    监听 on_chat_model_stream 事件，逐 token 返回。
    合规审查触发时，返回 interrupted 事件给前端弹出审批面板。

    Args:
        request: 聊天请求

    Returns:
        StreamingResponse: SSE 流式响应
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        """生成 SSE 事件流

        Yields:
            SSE 格式的事件（data: {...}\n\n）
            事件类型：
              - {"event": "node_start", "node": "...", "label": "..."}  — 节点开始
              - {"event": "node_end", "node": "...", "label": "..."}  — 节点完成
              - {"token": "..."}          — 逐字 token
              - {"status": "interrupted", "compliance_result": {...}}  — 合规中断
              - {"error": "..."}          — 错误
              - [DONE]                    — 流结束
        """
        # 节点名称 → 中文标签映射
        NODE_LABELS = {
            "intent_recognizer": "意图识别",
            "tool_selector": "工具选择",
            "data_fetcher": "数据获取",
            "analyzer": "分析计算",
            "compliance_checker": "合规审查",
            "response_generator": "生成回复",
        }
        try:
            # 1. 构建初始状态
            from langchain_core.messages import HumanMessage

            initial_state = {
                "messages": [HumanMessage(content=request.message)],
            }

            thread_id = request.session_id
            config = {"configurable": {"thread_id": thread_id}}

            print(f"\n{'='*60}")
            print(f"[LangGraph Stream] 用户消息: {request.message}")
            print(f"[LangGraph Stream] 会话 ID: {thread_id}")

            # 2. 流式执行，捕获合规中断
            try:
                async for event in get_graph().astream_events(
                    initial_state, config=config, version="v2"
                ):
                    # --- token 流（仅 response_generator 发出的 token 才转发给前端） ---
                    if event["event"] == "on_chat_model_stream":
                        # 检查是哪个节点在调用 LLM — 只有 response_generator 的 token 才是最终回复
                        node_name = event.get("metadata", {}).get("langgraph_node", "")
                        if node_name == "response_generator":
                            chunk = event["data"]["chunk"]
                            token = chunk.content
                            if not token:
                                continue
                            event_data = {"token": token}
                            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                    # --- 节点开始 ---
                    elif event["event"] == "on_chain_start":
                        node_name = event["name"]
                        if node_name in NODE_LABELS:
                            node_data = {"event": "node_start", "node": node_name, "label": NODE_LABELS[node_name]}
                            yield f"data: {json.dumps(node_data, ensure_ascii=False)}\n\n"
                            print(f"[LangGraph Stream] ▶ 节点: {NODE_LABELS[node_name]}")

                    elif event["event"] == "on_chain_end":
                        node_name = event["name"]
                        if node_name in NODE_LABELS:
                            node_data = {"event": "node_end", "node": node_name, "label": NODE_LABELS[node_name]}
                            yield f"data: {json.dumps(node_data, ensure_ascii=False)}\n\n"
                            print(f"[LangGraph Stream] ✓ 节点完成: {NODE_LABELS[node_name]}")

                # 3. 流式循环正常结束 — 检查是否被中断
                current = await get_graph().aget_state(config)
                pending = current.next  # 空列表 = 完成，非空 = 中断

                if pending:
                    # 图停在 compliance_checker 之后
                    compliance = current.values.get("compliance_result", {})
                    interrupted_data = {
                        "status": "interrupted",
                        "reply": f"⏸️ 合规审查 [{compliance.get('grade', '未知')}]，等待人工审批",
                        "compliance_result": compliance,
                        "pending_nodes": pending,
                    }
                    yield f"data: {json.dumps(interrupted_data, ensure_ascii=False)}\n\n"
                    print(f"[LangGraph Stream] 合规中断 → 等待审批")

            except GraphInterrupt as gi:
                # 4. GraphInterrupt 异常（interrupt_after 触发）
                current_state = await get_graph().aget_state(config)
                compliance = current_state.values.get("compliance_result", {})
                interrupted_data = {
                    "status": "interrupted",
                    "reply": f"⏸️ 合规审查 [{compliance.get('grade', '未知')}]，等待人工审批",
                    "compliance_result": compliance,
                }
                yield f"data: {json.dumps(interrupted_data, ensure_ascii=False)}\n\n"
                print(f"[LangGraph Stream] GraphInterrupt → 合规中断，等待审批")

            # 5. 流结束
            yield "data: [DONE]\n\n"
            print(f"[LangGraph Stream] 流式输出完成")

        except Exception as e:
            # 6. 错误处理
            error_msg = str(e)
            print(f"[LangGraph Stream] 错误: {error_msg}")
            import traceback

            traceback.print_exc()

            error_data = {"error": error_msg}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    # 返回 StreamingResponse
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "agent": "LangGraph"}


@router.get("/agent/graph/mermaid")
async def get_graph_mermaid():
    """获取状态图的 Mermaid 代码（可直接渲染）"""
    graph = get_graph()
    mermaid_code = graph.draw_mermaid()
    return {"mermaid": mermaid_code}


@router.get("/agent/graph/image")
async def get_graph_image():
    """获取状态图的 PNG 图片（base64 编码）"""
    import base64

    graph = get_graph()
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


# ── 基金净值历史（NavCard 折线图）──
@router.get("/api/funds/{fund_code}/nav-history")
async def get_nav_history(fund_code: str, range: str = "1m"):
    """获取基金净值历史数据
    
    Args:
        fund_code: 基金代码
        range: 时间范围 1w/1m/3m/6m/1y
    """
    # 先校验基金存在
    fund = fund_data_service.get_fund_info(fund_code)
    if not fund:
        raise HTTPException(status_code=404, detail=f"基金 {fund_code} 不存在")
    
    result = fund_data_service.get_fund_nav_history(fund_code, range)
    return {"code": 0, "data": result, "fund_name": fund.name}

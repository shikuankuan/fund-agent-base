"""
WebSocket 端点
支持双向通信：聊天消息、审批交互、工具调用状态反馈
"""

import asyncio
import json
import sys
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from langgraph.errors import GraphInterrupt

router = APIRouter()

# 节点名称 → 中文标签（与前端 ThinkingPipeline 保持一致）
NODE_LABELS = {
    "intent_recognizer": "意图识别",
    "tool_selector": "工具选择",
    "data_fetcher": "数据获取",
    "analyzer": "分析计算",
    "compliance_checker": "合规审查",
    "response_generator": "生成回复",
}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 主端点

    生命周期：
    1. 握手（accept）
    2. 循环接收客户端消息（chat / approval / ping）
    3. 对 chat 消息启动 LangGraph 流式执行
    4. 将 graph events 转为 JSON 消息发送
    5. 断线时清理
    """
    await websocket.accept()
    print(f"[WebSocket] ✅ 客户端已连接", flush=True)

    try:
        while True:
            # ── 接收消息（阻塞等待） ──
            print(f"[WebSocket] ⏳ 等待消息...", flush=True)
            raw = await websocket.receive_text()
            print(f"[WebSocket] 📩 收到原始消息: {raw[:200]}", flush=True)
            msg = json.loads(raw)
            msg_type = msg.get("type")
            print(f"[WebSocket] 消息类型: {msg_type}", flush=True)

            # ── 心跳 ──
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            # ── 聊天消息 ──
            if msg_type == "chat":
                payload = msg.get("payload", {})
                user_message = payload.get("message", "")
                session_id = payload.get("session_id", "default")

                print(f"\n{'='*60}", flush=True)
                print(f"[WebSocket] 收到消息: {user_message}", flush=True)
                print(f"[WebSocket] 会话 ID: {session_id}", flush=True)
                print(f"[WebSocket] 完整 payload: {payload}", flush=True)

                # 启动 LangGraph 流式执行
                print(f"[WebSocket] 🔧 开始调用 run_agent_stream...", flush=True)
                try:
                    await run_agent_stream(
                        websocket=websocket,
                        user_message=user_message,
                        session_id=session_id,
                    )
                    print(f"[WebSocket] ✅ run_agent_stream 正常返回", flush=True)
                except Exception as run_err:
                    print(f"[WebSocket] ❌ run_agent_stream 抛出异常: {run_err}", flush=True)
                    traceback.print_exc()
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "payload": {
                                "message": str(run_err),
                                "session_id": session_id,
                            },
                        })
                    except Exception:
                        pass

            # ── 审批消息 ──
            elif msg_type == "approval":
                payload = msg.get("payload", {})
                session_id = payload.get("session_id")
                action = payload.get("action")

                if not session_id or not action:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "approval 缺少 session_id 或 action"}
                    })
                    continue

                await handle_approval(websocket, session_id, action)

            # ── 未知消息类型 ──
            else:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": f"未知消息类型: {msg_type}"}
                })

    except WebSocketDisconnect:
        print(f"[WebSocket] ⚠️ 客户端断开连接", flush=True)
    except Exception as e:
        print(f"[WebSocket] ❌ 外层异常: {e}", flush=True)
        traceback.print_exc()


async def run_agent_stream(
    websocket: WebSocket,
    user_message: str,
    session_id: str,
):
    """
    核心：运行 LangGraph Agent 并将事件流转发到 WebSocket
    """
    from app.agent.graph import get_graph

    try:
        print(f"[run_agent_stream] ▶ 开始, msg={user_message[:40]}..., session={session_id}", flush=True)
        graph = get_graph()
        print(f"[run_agent_stream] get_graph() 返回: {type(graph).__name__}", flush=True)
        if graph is None:
            raise RuntimeError("get_graph() 返回 None，图未初始化")

        initial_state = {"messages": [HumanMessage(content=user_message)]}
        config = {"configurable": {"thread_id": session_id}}
        print(f"[run_agent_stream] 准备调用 astream_events...", flush=True)

        # ── 流式执行 LangGraph ──
        try:
            event_count = 0
            async for event in graph.astream_events(
                initial_state, config=config, version="v2"
            ):
                event_count += 1
                evt_type = event.get("event", "?")
                evt_name = event.get("name", "?")
                if event_count <= 5:
                    print(f"[run_agent_stream] 事件#{event_count}: type={evt_type} name={evt_name}", flush=True)

                # ① token 流（仅 response_generator 的 token）
                if evt_type == "on_chat_model_stream":
                    node_name = event.get("metadata", {}).get("langgraph_node", "")
                    if node_name == "response_generator":
                        chunk = event["data"]["chunk"]
                        token = chunk.content
                        if not token:
                            continue
                        print(f"[run_agent_stream] 💬 token: {token}", flush=True)
                        await websocket.send_json({
                            "type": "token",
                            "payload": {
                                "token": token,
                                "session_id": session_id,
                            },
                        })

                # ② 节点开始
                elif evt_type == "on_chain_start":
                    node_name = evt_name
                    if node_name in NODE_LABELS:
                        print(f"[run_agent_stream] ▶ 节点开始: {NODE_LABELS[node_name]}", flush=True)
                        await websocket.send_json({
                            "type": "node_start",
                            "payload": {
                                "node": node_name,
                                "label": NODE_LABELS[node_name],
                                "session_id": session_id,
                            },
                        })

                # ③ 节点结束
                elif evt_type == "on_chain_end":
                    node_name = evt_name
                    if node_name in NODE_LABELS:
                        print(f"[run_agent_stream] ✓ 节点完成: {NODE_LABELS[node_name]}", flush=True)
                        await websocket.send_json({
                            "type": "node_end",
                            "payload": {
                                "node": node_name,
                                "label": NODE_LABELS[node_name],
                                "session_id": session_id,
                            },
                        })

            print(f"[run_agent_stream] 流结束，共 {event_count} 个事件", flush=True)

            # ── 流正常结束 → 检查是否中断 ──
            current = await graph.aget_state(config)
            pending = current.next if current else None

            if pending:
                compliance = current.values.get("compliance_result", {})
                print(f"[run_agent_stream] ⏸️ 合规中断 grade={compliance.get('grade')}", flush=True)
                await websocket.send_json({
                    "type": "interrupted",
                    "payload": {
                        "compliance_result": compliance,
                        "session_id": session_id,
                    },
                })
            else:
                print(f"[run_agent_stream] ✅ 发送 done", flush=True)
                await websocket.send_json({
                    "type": "done",
                    "payload": {"session_id": session_id},
                })

        except GraphInterrupt:
            print(f"[run_agent_stream] ⚡ 捕获 GraphInterrupt", flush=True)
            current_state = await graph.aget_state(config)
            compliance = current_state.values.get("compliance_result", {})
            await websocket.send_json({
                "type": "interrupted",
                "payload": {
                    "compliance_result": compliance,
                    "session_id": session_id,
                },
            })

    except Exception as e:
        print(f"[run_agent_stream] ❌ 异常: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "payload": {
                    "message": f"{type(e).__name__}: {str(e)}",
                    "session_id": session_id,
                },
            })
        except Exception:
            print(f"[run_agent_stream] ❌ 连 error 消息都发不出去了", flush=True)


async def handle_approval(websocket: WebSocket, session_id: str, action: str):
    """
    处理审批：恢复 LangGraph 执行
    """
    from app.agent.graph import get_graph
    from langgraph.types import Command

    try:
        config = {"configurable": {"thread_id": session_id}}

        if action == "approve":
            async for event in get_graph().astream_events(
                Command(resume={"approved": True}),
                config=config,
                version="v2",
            ):
                evt_type = event.get("event", "")
                if evt_type == "on_chat_model_stream":
                    node_name = event.get("metadata", {}).get("langgraph_node", "")
                    if node_name == "response_generator":
                        chunk = event["data"]["chunk"]
                        token = chunk.content
                        if not token:
                            continue
                        await websocket.send_json({
                            "type": "token",
                            "payload": {
                                "token": token,
                                "session_id": session_id,
                            },
                        })
                elif evt_type == "on_chain_start":
                    node_name = event.get("name", "")
                    if node_name in NODE_LABELS:
                        await websocket.send_json({
                            "type": "node_start",
                            "payload": {
                                "node": node_name,
                                "label": NODE_LABELS[node_name],
                                "session_id": session_id,
                            },
                        })
                elif evt_type == "on_chain_end":
                    node_name = event.get("name", "")
                    if node_name in NODE_LABELS:
                        await websocket.send_json({
                            "type": "node_end",
                            "payload": {
                                "node": node_name,
                                "label": NODE_LABELS[node_name],
                                "session_id": session_id,
                            },
                        })

            await websocket.send_json({
                "type": "done",
                "payload": {"session_id": session_id},
            })

        elif action == "reject":
            await websocket.send_json({
                "type": "token",
                "payload": {
                    "token": "⛔ 您已驳回本次操作。根据合规审查结果，该操作已被终止。如需调整策略后重试，请重新发起对话。",
                    "session_id": session_id,
                },
            })
            await websocket.send_json({
                "type": "done",
                "payload": {"session_id": session_id},
            })
        else:
            await websocket.send_json({
                "type": "error",
                "payload": {"message": f"无效的审批操作: {action}"},
            })

    except Exception as e:
        print(f"[WebSocket] ❌ 审批处理异常: {e}", flush=True)
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "payload": {
                    "message": str(e),
                    "session_id": session_id,
                },
            })
        except Exception:
            pass

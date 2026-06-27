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

# 节点名称 → 中文标签
NODE_LABELS = {
    "intent_recognizer": "意图识别",
    "tool_selector": "工具选择",
    "data_fetcher": "数据获取",
    "analyzer": "分析计算",
    "compliance_checker": "合规审查",
    "response_generator": "生成回复",
}

# 条件路由映射： (from_node, to_node) → 中文标签
ROUTE_MAP = {
    ("intent_recognizer", "tool_selector"): "匹配到查询意图 → 工具选择",
    ("data_fetcher", "analyzer"): "有基金数据 → 分析计算",
    ("data_fetcher", "response_generator"): "无基金数据 → 直接回复",
    ("analyzer", "compliance_checker"): "含购买意图 → 合规审查",
    ("analyzer", "response_generator"): "无购买意图 → 直接回复",
}


def _safe_serialize(obj, max_str=2000):
    """安全序列化，截断超长字符串"""
    if isinstance(obj, (str, int, float, bool, type(None))):
        if isinstance(obj, str) and len(obj) > max_str:
            return obj[:max_str] + "..."
        return obj
    if isinstance(obj, dict):
        return {k: _safe_serialize(v, max_str) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_serialize(v, max_str) for v in obj[:20]]
    return str(obj)[:max_str]


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
                    print(
                        f"[WebSocket] ❌ run_agent_stream 抛出异常: {run_err}",
                        flush=True,
                    )
                    traceback.print_exc()
                    try:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "payload": {
                                    "message": str(run_err),
                                    "session_id": session_id,
                                },
                            }
                        )
                    except Exception:
                        pass

            # ── 审批消息 ──
            elif msg_type == "approval":
                payload = msg.get("payload", {})
                session_id = payload.get("session_id")
                action = payload.get("action")

                if not session_id or not action:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "payload": {
                                "message": "approval 缺少 session_id 或 action"
                            },
                        }
                    )
                    continue

                await handle_approval(websocket, session_id, action)

            # ── 未知消息类型 ──
            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "payload": {"message": f"未知消息类型: {msg_type}"},
                    }
                )

    except WebSocketDisconnect:
        print(f"[WebSocket] ⚠️ 客户端断开连接", flush=True)
    except RuntimeError as e:
        # Starlette 在连接已关闭时 receive_text() 抛出 RuntimeError
        if "not connected" in str(e).lower() or "close" in str(e).lower():
            print(f"[WebSocket] ⚠️ 连接已关闭", flush=True)
        else:
            traceback.print_exc()
    except Exception as e:
        print(f"[WebSocket] ❌ 外层异常: {e}", flush=True)
        traceback.print_exc()


# ====================================================================
# Reasoning Trace：根据 state 为每个节点生成推理过程文本
# ====================================================================


def _build_reasoning(node_name, vals):
    """根据 state 数据，为每个节点构造推理过程文本（Reasoning Trace）"""
    try:
        # ── 意图识别 ──
        if node_name == "intent_recognizer":
            msgs = vals.get("messages", [])
            user_msg = msgs[-1].content if msgs else ""
            intent = vals.get("user_intent", "?")
            return f"分析用户输入「{user_msg[:80]}」→ 判断为 {intent} 意图"

        # ── 工具选择 ──
        elif node_name == "tool_selector":
            intent = vals.get("user_intent", "?")
            tools = vals.get("selected_tools", []) or []
            tool_names = ", ".join(tools[:5])
            more = f"... 等{len(tools)}个" if len(tools) > 5 else ""
            return f"意图为 {intent}，根据工具映射表选择：{tool_names}{more}"

        # ── 数据获取 ──
        elif node_name == "data_fetcher":
            fi = vals.get("fund_info")
            af = vals.get("all_funds", []) or []
            codes = vals.get("fund_codes", []) or []

            lines = []
            if codes:
                lines.append(f"扫描到基金代码：{', '.join(codes)}")
            else:
                lines.append("未发现基金代码，执行全库查询")

            if fi:
                code = (
                    fi.code
                    if hasattr(fi, "code")
                    else fi.get("code", "") if isinstance(fi, dict) else ""
                )
                name = (
                    fi.name
                    if hasattr(fi, "name")
                    else fi.get("name", "") if isinstance(fi, dict) else ""
                )
                risk = (
                    fi.risk_level
                    if hasattr(fi, "risk_level")
                    else fi.get("risk_level", "") if isinstance(fi, dict) else ""
                )
                lines.append(f"查询成功：{code} {name}（{risk}）")
            if af:
                names = []
                for f in af:
                    n = (
                        f.get("name", "")
                        if isinstance(f, dict)
                        else (f.name if hasattr(f, "name") else "")
                    )
                    if n:
                        names.append(n)
                if names:
                    lines.append(
                        f"全库共 {len(af)} 只基金：{'、'.join(names[:3])}{'...' if len(names) > 3 else ''}"
                    )
            if not lines:
                return "未获取到基金数据"
            return "\n".join(lines)

        # ── 分析计算 ──
        elif node_name == "analyzer":
            ar = vals.get("analysis_result", {}) or {}
            if not ar:
                return "无分析数据"

            perf = ar.get("performance", {}) or {}
            risk = ar.get("risk", {}) or {}
            mgr = ar.get("manager", {}) or {}
            name = ar.get("fund_name", ar.get("name", ""))

            lines = [f"分析标的：{name}"] if name else []
            if perf:
                ret = perf.get("return_1y", perf.get("annual_return"))
                sharpe = perf.get("sharpe_ratio")
                if ret is not None:
                    lines.append(f"近1年收益：{ret*100 if abs(ret) < 10 else ret:.2f}%")
                if sharpe is not None:
                    lines.append(f"Sharpe比率：{sharpe}")
            if risk:
                dd = risk.get("max_drawdown")
                beta = risk.get("beta")
                level = risk.get("risk_level", "")
                if dd is not None:
                    lines.append(f"最大回撤：{dd*100 if abs(dd) < 10 else dd:.2f}%")
                if beta is not None:
                    lines.append(f"Beta系数：{beta}")
                if level:
                    if lines:
                        lines[-1] += f"（{level}）"
                    else:
                        lines.append(f"风险等级：{level}")
            if mgr and mgr.get("name"):
                lines.append(
                    f"基金经理：{mgr['name']}（任职{mgr.get('tenure_years', '?')}年）"
                )

            comparison = ar.get("comparison", [])
            if comparison:
                cmp_names = []
                for c in comparison:
                    n = c.get("name", "") or c.get("code", "")
                    if n:
                        cmp_names.append(n)
                lines.append(
                    f"对比额外 {len(comparison)} 只基金：{'、'.join(cmp_names[:3])}{'...' if len(cmp_names) > 3 else ''}"
                )

            return "\n".join(lines) if lines else "分析完成"

        # ── 合规审查 ──
        elif node_name == "compliance_checker":
            cr = vals.get("compliance_result", {}) or {}
            checks = cr.get("checks", [])
            if not checks:
                return "未执行合规检查"
            lines = []
            for c in checks:
                name = c.get("name", "")
                passed = c.get("passed", True)
                detail = c.get("detail", "")
                icon = "✅" if passed else "❌"
                lines.append(f"{icon} {name}：{detail}")
            return "\n".join(lines)

        # ── 生成回复 ──
        elif node_name == "response_generator":
            intent = vals.get("user_intent", "query")
            ar = vals.get("analysis_result")
            cr = vals.get("compliance_result")
            parts = [f"基于 {intent} 意图"]
            if ar:
                parts.append("结合分析结果")
            if cr:
                grade = cr.get("grade", "pass") if isinstance(cr, dict) else "?"
                parts.append(f"合规结论：{grade}")
            return "、".join(parts) + " → 生成自然语言回复"

    except Exception as e:
        return f"推理生成失败: {e}"

    return ""


async def _build_node_summary(graph, config, node_name):
    """读取 state，为节点构造摘要 + 推理过程 + 路由标签"""
    result = {}
    try:
        state = await graph.aget_state(config)
        if not state or not state.values:
            return result
        vals = state.values

        if node_name == "intent_recognizer":
            result["summary"] = str(vals.get("user_intent", "?"))

        elif node_name == "tool_selector":
            tools = vals.get("selected_tools", []) or []
            result["tools"] = tools
            result["summary"] = f"{len(tools)} 个工具"

        elif node_name == "data_fetcher":
            fi = vals.get("fund_info")
            af = vals.get("all_funds", []) or []
            if fi:
                name = (
                    fi.name
                    if hasattr(fi, "name")
                    else fi.get("name", "") if isinstance(fi, dict) else ""
                )
            else:
                name = ""
            result["summary"] = name or f"获取 {len(af)} 只基金"
            result["fund_count"] = len(af)

        elif node_name == "analyzer":
            ar = vals.get("analysis_result", {}) or {}
            parts = []
            if ar.get("annual_return") is not None:
                try:
                    v = float(ar["annual_return"])
                    parts.append(f"年化 {v*100:.1f}%" if v < 10 else f"年化 {v:.1f}%")
                except (ValueError, TypeError):
                    pass
            if ar.get("sharpe_ratio") is not None:
                parts.append(f"Sharpe {ar['sharpe_ratio']}")
            result["summary"] = "，".join(parts) if parts else "分析完成"

        elif node_name == "compliance_checker":
            cr = vals.get("compliance_result", {}) or {}
            grade = cr.get("grade", "pass")
            result["summary"] = f"审查：{grade}"
            result["grade"] = grade

        elif node_name == "response_generator":
            result["summary"] = ""

        # ── 推理过程 ──
        result["reasoning"] = _build_reasoning(node_name, vals)

        # ── 条件路由 ──
        if node_name != "response_generator":
            next_nodes = state.next
            if next_nodes:
                for nxt in next_nodes:
                    route = ROUTE_MAP.get((node_name, nxt))
                    if route:
                        result["route"] = route
                        result["next_node"] = nxt
                        break

    except Exception as e:
        print(f"[node_summary] ⚠️ {node_name} 摘要失败: {e}", flush=True)
    return result


# ====================================================================
# LangGraph 流式执行
# ====================================================================


async def run_agent_stream(websocket: WebSocket, user_message: str, session_id: str):
    """运行 LangGraph 并流式推送事件"""
    from app.agent.graph import get_graph
    from app.agent.state import AgentState
    from langchain_core.messages import HumanMessage

    print(f"[run_agent_stream] 🏃 开始执行", flush=True)
    graph = get_graph()
    config = {"configurable": {"thread_id": session_id}}

    # 事件计数
    event_count = 0

    try:
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=user_message)]},
            config=config,
            version="v2",
        ):
            event_count += 1
            evt_type = event.get("event", "")
            node_name = event.get("metadata", {}).get("langgraph_node", "")
            label = NODE_LABELS.get(node_name, node_name)

            # ── 节点开始 ──
            if evt_type == "on_chain_start" and node_name:
                print(
                    f"[run_agent_stream] 🔵 节点开始: {node_name} (#{event_count})",
                    flush=True,
                )
                await websocket.send_json(
                    {
                        "type": "node_start",
                        "payload": {"node": node_name, "label": label},
                    }
                )

            # ── 节点结束 ──
            elif evt_type == "on_chain_end" and node_name:
                summary = await _build_node_summary(graph, config, node_name)
                print(
                    f"[run_agent_stream] 🟢 节点结束: {node_name} | summary={summary.get('summary','')[:60]}",
                    flush=True,
                )
                await websocket.send_json(
                    {
                        "type": "node_end",
                        "payload": {
                            "node": node_name,
                            "label": label,
                            **summary,
                        },
                    }
                )

            # ── LLM 流式 token（仅 response_generator） ──
            elif evt_type == "on_chat_model_stream":
                chunk_node = event.get("metadata", {}).get("langgraph_node", "")
                if chunk_node == "response_generator":
                    chunk = event["data"]["chunk"]
                    token = chunk.content
                    if token:
                        await websocket.send_json(
                            {
                                "type": "token",
                                "payload": {
                                    "token": token,
                                    "session_id": session_id,
                                },
                            }
                        )

        # 发送完成
        print(
            f"[run_agent_stream] ✅ 流式完成，共 {event_count} 个事件",
            flush=True,
        )
        await websocket.send_json(
            {
                "type": "done",
                "payload": {"session_id": session_id},
            }
        )

    except WebSocketDisconnect:
        print(f"[run_agent_stream] ⚡ 客户端断开，流式终止", flush=True)
        return

    except GraphInterrupt:
        print(f"[run_agent_stream] ⚡ 捕获 GraphInterrupt", flush=True)
        current_state = await graph.aget_state(config)
        compliance = current_state.values.get("compliance_result", {})
        await websocket.send_json(
            {
                "type": "interrupted",
                "payload": {
                    "compliance_result": compliance,
                    "session_id": session_id,
                },
            }
        )

    except Exception as e:
        print(f"[run_agent_stream] ❌ 异常: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "payload": {
                        "message": f"{type(e).__name__}: {str(e)}",
                        "session_id": session_id,
                    },
                }
            )
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
                        if token:
                            await websocket.send_json(
                                {
                                    "type": "token",
                                    "payload": {
                                        "token": token,
                                        "session_id": session_id,
                                    },
                                }
                            )
            await websocket.send_json(
                {"type": "done", "payload": {"session_id": session_id}}
            )

        elif action == "reject":
            await websocket.send_json(
                {
                    "type": "token",
                    "payload": {
                        "token": "⚠️ 审批未通过，请求已被驳回。如有疑问请联系合规部门。",
                        "session_id": session_id,
                    },
                }
            )
            await websocket.send_json(
                {"type": "done", "payload": {"session_id": session_id}}
            )

    except WebSocketDisconnect:
        print(f"[handle_approval] ⚡ 客户端断开", flush=True)
    except Exception as e:
        print(f"[handle_approval] ❌ {e}", flush=True)
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "payload": {
                        "message": f"审批错误: {str(e)}",
                        "session_id": session_id,
                    },
                }
            )
        except Exception:
            pass

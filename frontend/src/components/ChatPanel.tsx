import React, { useState, useRef, useEffect, useCallback } from "react";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import ApprovalPanel from "./ApprovalPanel";
import AgentFlow, { type NodeSummary } from "./AgentFlow";
import { useWebSocket } from "@/hooks/useWebSocket";
import { buildChatMessage, buildApprovalMessage } from "@/services/ws";
import type { WsMessage } from "@/hooks/useWebSocket";
import type { ComplianceResult } from "@/services";

// ===== 消息类型 =====
interface Message {
    role: "user" | "assistant";
    content: string;
    compliance?: ComplianceResult;
    timestamp: string;
    pipelineNodes?: NodeSummary[]; // 本消息对应的执行流程
}

// ===== 会话 ID =====
const makeSessionId = () =>
    `web-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

// ===== Props =====
interface ChatPanelProps {
    activeSession: string;
}

const WS_URL = `ws://localhost:8000/ws`;

// 最小显示时长（毫秒）
const MIN_NODE_VISIBLE_MS = 500;

const ChatPanel: React.FC<ChatPanelProps> = ({ activeSession }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [streaming, setStreaming] = useState(false);
    const [interrupted, setInterrupted] = useState(false);
    const [sessionId] = useState(makeSessionId);
    const bottomRef = useRef<HTMLDivElement>(null);
    const currentMsgIndexRef = useRef<number>(0);

    // 执行流程节点
    const [pipelineNodes, setPipelineNodes] = useState<NodeSummary[]>([]);
    const pipelineNodesRef = useRef<NodeSummary[]>([]);

    // 记录每个节点的 active 开始时间（处理 0.5s 最小可见）
    const activeTimestamps = useRef<Map<string, number>>(new Map());
    const doneTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

    // 追踪是否已收到第一个 token（用于标记 response_generator done）
    const firstTokenReceived = useRef(false);

    // 同步 ref
    useEffect(() => {
        pipelineNodesRef.current = pipelineNodes;
    }, [pipelineNodes]);

    // 组件卸载时清除所有定时器
    useEffect(() => {
        return () => {
            doneTimers.current.forEach((t) => clearTimeout(t));
        };
    }, []);

    // ── WebSocket 连接 ──
    const { status, send, on } = useWebSocket({
        url: WS_URL,
        autoConnect: true,
    });

    // 自动滚到底部
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, pipelineNodes]);

    // ── 注册 WebSocket 消息处理器 ──
    useEffect(() => {
        // ① 流式 token
        const unsubToken = on("token", (msg: WsMessage) => {
            const token = msg.payload.token as string;
            if (!token) return;

            // 追加 token 到消息
            setMessages((prev) => {
                const updated = [...prev];
                const idx = currentMsgIndexRef.current;
                const target = updated[idx];
                if (target && target.role === "assistant") {
                    updated[idx] = { ...target, content: target.content + token };
                }
                return updated;
            });

            // 第一个 token：标记 response_generator 为 done，清空摘要
            if (!firstTokenReceived.current) {
                firstTokenReceived.current = true;
                setPipelineNodes((prev) =>
                    prev.map((n) =>
                        n.node === "response_generator"
                            ? { ...n, status: "done", summary: undefined }
                            : n,
                    ),
                );
            }
        });

        // ② 节点开始 → 记录时间 + 添加 active 节点
        const unsubNodeStart = on("node_start", (msg: WsMessage) => {
            const node = msg.payload.node as string;
            const label = msg.payload.label as string;
            activeTimestamps.current.set(node, Date.now());

            setPipelineNodes((prev) => {
                // 避免重复添加
                if (prev.some((n) => n.node === node)) return prev;
                return [...prev, { node, label, status: "active" }];
            });
        });

        // ③ 节点结束 → 填充摘要 + 路由信息；非 response_generator 0.5s 最小可见
        const unsubNodeEnd = on("node_end", (msg: WsMessage) => {
            const node = msg.payload.node as string;
            const label = msg.payload.label as string;
            const summary = msg.payload.summary as string | undefined;
            const tools = msg.payload.tools as string[] | undefined;
            const grade = msg.payload.grade as string | undefined;
            const fund_count = msg.payload.fund_count as number | undefined;
            const route = msg.payload.route as string | undefined;
            const nextNode = msg.payload.next_node as string | undefined;
            const reasoning = msg.payload.reasoning as string | undefined;

            // 填充摘要/路由/推理数据（保持 active 状态）
            setPipelineNodes((prev) =>
                prev.map((n) =>
                    n.node === node
                        ? { ...n, summary, tools, grade, fund_count, route, nextNode, reasoning }
                        : n,
                ),
            );

            // response_generator：不在 node_end 时切换 done，由 token 事件处理
            if (node === "response_generator") return;

            const activeAt = activeTimestamps.current.get(node) || Date.now();
            const elapsed = Date.now() - activeAt;
            const remaining = Math.max(0, MIN_NODE_VISIBLE_MS - elapsed);

            const markDone = () => {
                setPipelineNodes((prev) =>
                    prev.map((n) =>
                        n.node === node ? { ...n, status: "done" } : n,
                    ),
                );
                doneTimers.current.delete(node);
            };

            if (remaining > 0) {
                const existing = doneTimers.current.get(node);
                if (existing) clearTimeout(existing);
                doneTimers.current.set(node, setTimeout(markDone, remaining));
            } else {
                markDone();
            }
        });

        // ④ 合规中断
        const unsubInterrupted = on("interrupted", (msg: WsMessage) => {
            setStreaming(false);
            setInterrupted(true);
            const cr = msg.payload.compliance_result as ComplianceResult | undefined;
            setMessages((prev) => {
                const updated = [...prev];
                const idx = currentMsgIndexRef.current;
                const target = updated[idx];
                if (target && target.role === "assistant") {
                    updated[idx] = { ...target, compliance: cr };
                }
                return updated;
            });
        });

        // ⑤ 流结束
        const unsubDone = on("done", () => {
            setStreaming(false);
            // 把流程节点固化为当前消息的一部分
            setMessages((prev) => {
                const updated = [...prev];
                const idx = currentMsgIndexRef.current;
                const target = updated[idx];
                if (target && target.role === "assistant") {
                    updated[idx] = {
                        ...target,
                        pipelineNodes: pipelineNodesRef.current.filter((n) => n.status === "done"),
                    };
                }
                return updated;
            });
            setPipelineNodes([]);
            activeTimestamps.current.clear();
            firstTokenReceived.current = false;
        });

        // ⑥ 错误
        const unsubError = on("error", (msg: WsMessage) => {
            setStreaming(false);
            setPipelineNodes([]);
            activeTimestamps.current.clear();
            firstTokenReceived.current = false;
            const errMsg = (msg.payload.message as string) || "未知错误";
            setMessages((prev) => {
                const updated = [...prev];
                const idx = currentMsgIndexRef.current;
                const target = updated[idx];
                if (target && target.role === "assistant") {
                    updated[idx] = {
                        ...target,
                        content: target.content + `\n\n❌ ${errMsg}`,
                    };
                }
                return updated;
            });
        });

        return () => {
            unsubToken();
            unsubNodeStart();
            unsubNodeEnd();
            unsubInterrupted();
            unsubDone();
            unsubError();
        };
    }, [on]);

    /** 发送消息（WebSocket） */
    const handleSend = useCallback(
        (text: string) => {
            const userMsg: Message = {
                role: "user",
                content: text,
                timestamp: new Date().toLocaleTimeString(),
            };
            const assistantMsg: Message = {
                role: "assistant",
                content: "",
                timestamp: new Date().toLocaleTimeString(),
            };

            setMessages((prev) => {
                currentMsgIndexRef.current = prev.length + 1;
                return [...prev, userMsg, assistantMsg];
            });
            setStreaming(true);
            setInterrupted(false);
            setPipelineNodes([]);
            activeTimestamps.current.clear();
            firstTokenReceived.current = false;
            doneTimers.current.forEach((t) => clearTimeout(t));
            doneTimers.current.clear();

            send(buildChatMessage(text, sessionId));
        },
        [send, sessionId],
    );

    /** 审批提交（WebSocket） */
    const handleApprovalResolved = useCallback(
        (action: "approve" | "reject") => {
            setInterrupted(false);
            send(buildApprovalMessage(sessionId, action));
        },
        [send, sessionId],
    );

    const isEmpty = messages.length === 0;

    return (
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            {/* 消息列表 */}
            <div style={{ flex: 1, overflow: "auto", padding: 20 }}>
                {isEmpty && (
                    <div
                        style={{
                            textAlign: "center",
                            color: "#9ca3af",
                            marginTop: 120,
                            fontSize: 14,
                            lineHeight: 2,
                        }}
                    >
                        <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}>🏦</div>
                        <div>你好！我是基金智能助手</div>
                        <div style={{ fontSize: 12 }}>可以帮你查基金、分析风险、验证合规</div>
                    </div>
                )}

                {messages.map((msg, i) => {
                    const isLast = i === messages.length - 1;
                    const isLastAssistant = isLast && msg.role === "assistant";

                    // 最后一条 assistant 且正在流式 → 显示实时 pipelineNodes
                    // 否则显示消息固化的 pipelineNodes
                    const showNodes =
                        isLastAssistant && streaming
                            ? pipelineNodes
                            : msg.pipelineNodes || [];

                    return (
                        <div key={i}>
                            {/* Agent 执行流程 → 在气泡上方 */}
                            {showNodes.length > 0 && <AgentFlow nodes={showNodes} />}

                            <ChatBubble
                                role={msg.role}
                                content={
                                    msg.content ||
                                    (isLastAssistant && streaming ? "思考中..." : "")
                                }
                                timestamp={msg.timestamp}
                            />

                            {/* 合规审批 */}
                            {msg.compliance && (
                                <ApprovalPanel
                                    sessionId={sessionId}
                                    compliance={msg.compliance}
                                    onResolved={(action: "approve" | "reject") => {
                                        setInterrupted(false);
                                        setStreaming(true);
                                        setPipelineNodes([]);
                                        activeTimestamps.current.clear();
                                        firstTokenReceived.current = false;
                                        setMessages((prev) => {
                                            const updated = [...prev];
                                            const last = updated[updated.length - 1];
                                            if (last.role === "assistant") {
                                                updated[updated.length - 1] = {
                                                    ...last,
                                                    content: "",
                                                    compliance: undefined,
                                                };
                                                currentMsgIndexRef.current = updated.length - 1;
                                            }
                                            return updated;
                                        });
                                        handleApprovalResolved(action);
                                    }}
                                />
                            )}
                        </div>
                    );
                })}

                <div ref={bottomRef} />
            </div>

            {/* 输入区域 */}
            <ChatInput onSend={handleSend} disabled={streaming && !interrupted} />
        </div>
    );
};

export default ChatPanel;

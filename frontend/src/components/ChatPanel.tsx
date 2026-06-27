import React, { useState, useRef, useEffect, useCallback } from "react";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import ApprovalPanel from "./ApprovalPanel";
import ThinkingPipeline from "./ThinkingPipeline";
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
}

// ===== 会话 ID =====
const makeSessionId = () =>
    `web-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

// ===== Props =====
interface ChatPanelProps {
    activeSession: string;
}

const WS_URL = `ws://localhost:8000/ws`;

const ChatPanel: React.FC<ChatPanelProps> = ({ activeSession }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [streaming, setStreaming] = useState(false);
    const [interrupted, setInterrupted] = useState(false);
    const [sessionId] = useState(makeSessionId);
    const bottomRef = useRef<HTMLDivElement>(null);
    const currentMsgIndexRef = useRef<number>(0);

    // 管道状态
    const [activeNode, setActiveNode] = useState<string | null>(null);
    const [completedNodes, setCompletedNodes] = useState<Set<string>>(new Set());
    const [hasFirstToken, setHasFirstToken] = useState(false);
    const [pipelineDone, setPipelineDone] = useState(false);

    // ── WebSocket 连接 ──
    const { status, send, on } = useWebSocket({
        url: WS_URL,
        autoConnect: true,
    });

    // 自动滚到底部
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // ── 注册 WebSocket 消息处理器（只执行一次） ──
    useEffect(() => {
        const unsubToken = on("token", (msg: WsMessage) => {
            const token = msg.payload.token as string;
            if (!token) return;

            setHasFirstToken(true);
            setMessages((prev) => {
                const updated = [...prev];
                const idx = currentMsgIndexRef.current;
                const target = updated[idx];
                if (target && target.role === "assistant") {
                    updated[idx] = {
                        ...target,
                        content: target.content + token,
                    };
                }
                return updated;
            });
        });

        const unsubNodeStart = on("node_start", (msg: WsMessage) => {
            const node = msg.payload.node as string;
            setActiveNode(node);
        });

        const unsubNodeEnd = on("node_end", (msg: WsMessage) => {
            const node = msg.payload.node as string;
            setCompletedNodes((prev) => {
                const next = new Set(prev);
                next.add(node);
                return next;
            });
            setActiveNode(null);
            if (node === "response_generator") {
                setPipelineDone(true);
            }
        });

        const unsubInterrupted = on("interrupted", (msg: WsMessage) => {
            setStreaming(false);
            setInterrupted(true);
            const cr = msg.payload.compliance_result as ComplianceResult | undefined;
            setMessages((prev) => {
                const updated = [...prev];
                const idx = currentMsgIndexRef.current;
                const target = updated[idx];
                if (target && target.role === "assistant") {
                    updated[idx] = {
                        ...target,
                        compliance: cr,
                    };
                }
                return updated;
            });
        });

        const unsubDone = on("done", () => {
            setStreaming(false);
            setActiveNode(null);
        });

        const unsubError = on("error", (msg: WsMessage) => {
            setStreaming(false);
            setActiveNode(null);
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
                currentMsgIndexRef.current = prev.length + 1; // user message at len, assistant at len+1
                return [...prev, userMsg, assistantMsg];
            });
            setStreaming(true);
            setInterrupted(false);
            setHasFirstToken(false);
            setActiveNode(null);
            setCompletedNodes(new Set());
            setPipelineDone(false);

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

                {messages.map((msg, i) => (
                    <div key={i}>
                        {/* 管道：在最后一条 assistant 消息上方，只要管道没结束就一直显示 */}
                        {streaming && !pipelineDone && !interrupted && i === messages.length - 1 && msg.role === "assistant" && (
                            <ThinkingPipeline activeNode={activeNode} completedNodes={completedNodes} />
                        )}
                        <ChatBubble
                            role={msg.role}
                            content={msg.content || (streaming && i === messages.length - 1 ? "▊" : "")}
                            timestamp={msg.timestamp}
                        />
                        {/* 流式中已输出 token → 显示状态条 */}
                        {streaming && hasFirstToken && !pipelineDone && !interrupted && i === messages.length - 1 && msg.role === "assistant" && (
                            <div style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 8,
                                marginTop: 8,
                                paddingLeft: 60,
                            }}>
                                <span style={{ fontSize: 11, color: "#1677ff", fontWeight: 500 }}>
                                    ⚙️ 正在生成回复
                                </span>
                                <span style={{
                                    display: "inline-block",
                                    width: 6,
                                    height: 6,
                                    borderRadius: "50%",
                                    background: "#1677ff",
                                    animation: "typingDot 1s ease-in-out infinite",
                                }} />
                            </div>
                        )}
                        {msg.compliance && (
                            <ApprovalPanel
                                sessionId={sessionId}
                                compliance={msg.compliance}
                                onResolved={(action: "approve" | "reject") => {
                                    setInterrupted(false);
                                    setStreaming(true);
                                    // 清空当前助手消息内容，等待 WebSocket 新 token 流
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
                                    // 通过 WebSocket 发送审批决定
                                    handleApprovalResolved(action);
                                }}
                            />
                        )}
                    </div>
                ))}

                {/* 管道：刚发完消息（最后一条是 user）→ 在底部显示 */}
                {streaming && !pipelineDone && !interrupted && messages.length > 0 && messages[messages.length - 1]?.role === "user" && (
                    <ThinkingPipeline activeNode={activeNode} completedNodes={completedNodes} />
                )}

                <div ref={bottomRef} />
            </div>

            {/* 输入区域 */}
            <ChatInput onSend={handleSend} disabled={streaming && !interrupted} />

            {/* 动画定义 */}
            <style>{`
                @keyframes typingDot {
                    0%, 100% { opacity: 0.3; transform: scale(0.8); }
                    50% { opacity: 1; transform: scale(1.2); }
                }
            `}</style>
        </div>
    );
};

export default ChatPanel;

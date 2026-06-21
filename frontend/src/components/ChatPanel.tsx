import React, { useState, useRef, useEffect, useCallback } from "react";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import ApprovalPanel from "./ApprovalPanel";
import ThinkingPipeline from "./ThinkingPipeline";
import { sendMessageStream } from "@/services";
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

const ChatPanel: React.FC<ChatPanelProps> = ({ activeSession }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [streaming, setStreaming] = useState(false);
    const [interrupted, setInterrupted] = useState(false);
    const [sessionId] = useState(makeSessionId);
    const bottomRef = useRef<HTMLDivElement>(null);
    const abortRef = useRef<(() => void) | null>(null);

    // 管道状态
    const [activeNode, setActiveNode] = useState<string | null>(null);
    const [completedNodes, setCompletedNodes] = useState<Set<string>>(new Set());
    const [hasFirstToken, setHasFirstToken] = useState(false);
    const [pipelineDone, setPipelineDone] = useState(false);

    // 自动滚到底部
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    /** 发送消息（SSE 流式） */
    const handleSend = useCallback(
        (text: string) => {
            const userMsg: Message = {
                role: "user",
                content: text,
                timestamp: new Date().toLocaleTimeString(),
            };
            // 空占位，逐字填充
            const assistantMsg: Message = {
                role: "assistant",
                content: "",
                timestamp: new Date().toLocaleTimeString(),
            };

            setMessages((prev) => [...prev, userMsg, assistantMsg]);
            setStreaming(true);
            setInterrupted(false);
            setHasFirstToken(false);
            setActiveNode(null);
            setCompletedNodes(new Set());
            setPipelineDone(false);

            // 拿到当前消息索引（闭包）
            const currentLen = messages.length + 1; // 加了 user + assistant

            const { abort } = sendMessageStream(
                { message: text, session_id: sessionId },

                // onToken —— 逐字追加
                (token: string) => {
                    setHasFirstToken(true);
                    setMessages((prev) => {
                        const updated = [...prev];
                        const target = updated[currentLen];
                        if (target && target.role === "assistant") {
                            updated[currentLen] = {
                                ...target,
                                content: target.content + token,
                            };
                        }
                        return updated;
                    });
                },

                // onInterrupted —— 合规中断，弹出审批面板
                (data) => {
                    setStreaming(false);
                    setInterrupted(true);
                    setMessages((prev) => {
                        const updated = [...prev];
                        const target = updated[currentLen];
                        if (target && target.role === "assistant") {
                            updated[currentLen] = {
                                ...target,
                                content: data.reply || "（等待审批）",
                                compliance: data.compliance_result,
                            };
                        }
                        return updated;
                    });
                },

                // onDone
                () => {
                    setStreaming(false);
                    setActiveNode(null);
                },

                // onError
                (err: string) => {
                    setStreaming(false);
                    setActiveNode(null);
                    setMessages((prev) => {
                        const updated = [...prev];
                        const target = updated[currentLen];
                        if (target && target.role === "assistant") {
                            updated[currentLen] = {
                                ...target,
                                content: `❌ ${err}`,
                            };
                        }
                        return updated;
                    });
                },

                // onNodeEvent —— 管道节点状态
                (event) => {
                    if (event.type === "start") {
                        setActiveNode(event.node);
                    } else if (event.type === "end") {
                        setCompletedNodes((prev) => {
                            const next = new Set(prev);
                            next.add(event.node);
                            return next;
                        });
                        setActiveNode(null);
                        // response_generator 完成 → 管道使命结束
                        if (event.node === "response_generator") {
                            setPipelineDone(true);
                        }
                    }
                },
            );

            abortRef.current = abort;
        },
        [messages.length, sessionId],
    );

    /** 审批完成后更新最后一条 AI 消息 */
    const handleApprovalResolved = useCallback((reply: string) => {
        setInterrupted(false);
        setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.role === "assistant") {
                updated[updated.length - 1] = {
                    ...last,
                    content: reply,
                    compliance: undefined,
                };
            }
            return updated;
        });
    }, []);

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
                                onResolved={handleApprovalResolved}
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

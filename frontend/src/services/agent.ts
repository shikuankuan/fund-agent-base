/**
 * Agent 服务层
 * 封装基金智能助手后端接口
 */

import http from "./http";

// ===== 类型定义 =====

export interface ChatRequest {
    message: string;
    session_id: string;
}

export interface ChatResponse {
    reply: string;
    session_id: string;
    status: "completed" | "interrupted" | "resumed" | "rejected";
    compliance_result?: ComplianceResult;
    pending_nodes?: string[];
}

export interface ComplianceResult {
    grade: "pass" | "warn" | "block";
    overall_passed: boolean;
    checks: ComplianceCheck[];
}

export interface ComplianceCheck {
    name: string;
    passed: boolean;
    severity: "pass" | "warn" | "block";
    detail: string;
}

export interface ApprovalRequest {
    session_id: string;
    action: "approve" | "reject";
}

export interface ApprovalResponse {
    reply: string;
    status: string;
}

// ===== API 函数 =====

/** 发送消息（非流式） */
export function sendMessage(payload: ChatRequest): Promise<ChatResponse> {
    return http.post<ChatResponse>("/chat", payload);
}

/** 发送消息（SSE 流式） */
export function sendMessageStream(
    payload: ChatRequest,
    onToken: (token: string) => void,
    onInterrupted: (data: ChatResponse) => void,
    onDone: () => void,
    onError: (err: string) => void,
    onNodeEvent?: (event: { type: "start" | "end"; node: string; label: string }) => void,
): { abort: () => void } {
    const controller = new AbortController();

    (async () => {
        try {
            const res = await fetch("/api/chat/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                signal: controller.signal,
            });

            if (!res.ok) {
                onError(`HTTP ${res.status}: ${res.statusText}`);
                return;
            }

            const reader = res.body?.getReader();
            if (!reader) {
                onError("浏览器不支持流式响应");
                return;
            }

            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    const payload = line.slice(6).trim();

                    if (payload === "[DONE]") {
                        onDone();
                        return;
                    }

                    try {
                        const data = JSON.parse(payload);
                        if (data.event === "node_start" && onNodeEvent) {
                            onNodeEvent({ type: "start", node: data.node, label: data.label });
                        } else if (data.event === "node_end" && onNodeEvent) {
                            onNodeEvent({ type: "end", node: data.node, label: data.label });
                        } else if (data.token) {
                            onToken(data.token);
                        } else if (data.status === "interrupted") {
                            onInterrupted(data);
                            return;
                        } else if (data.error) {
                            onError(data.error);
                            return;
                        }
                    } catch {
                        // 非 JSON，忽略
                    }
                }
            }
            onDone();
        } catch (err) {
            if ((err as Error).name === "AbortError") return;
            onError(`网络错误: ${(err as Error).message}`);
        }
    })();

    return { abort: () => controller.abort() };
}

/** 提交审批 */
export function submitApproval(payload: ApprovalRequest): Promise<ApprovalResponse> {
    return http.post<ApprovalResponse>("/approval", payload);
}

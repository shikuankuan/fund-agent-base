const BASE = "http://localhost:8000/api";

// ===== 类型定义 =====

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

// ===== 非流式聊天 =====

export async function sendMessage(
    message: string,
    sessionId: string,
): Promise<ChatResponse> {
    const res = await fetch(`${BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId }),
    });
    return res.json();
}

// ===== 流式聊天（SSE） =====

export async function sendMessageStream(
    message: string,
    sessionId: string,
    onToken: (token: string) => void,
    onInterrupted: (data: ChatResponse) => void,
    onDone: () => void,
    onError: (err: string) => void,
): Promise<void> {
    const res = await fetch(`${BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, session_id: sessionId }),
    });

    if (!res.ok) {
        onError(`HTTP ${res.status}`);
        return;
    }

    const reader = res.body?.getReader();
    if (!reader) {
        onError("无法读取响应流");
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
                if (data.token) {
                    onToken(data.token);
                } else if (data.status === "interrupted") {
                    onInterrupted(data);
                    return;
                } else if (data.error) {
                    onError(data.error);
                    return;
                }
            } catch {
                // 非 JSON 行忽略
            }
        }
    }
    onDone();
}

// ===== 人工审批 =====

export async function submitApproval(
    sessionId: string,
    action: "approve" | "reject",
): Promise<{ reply: string; status: string }> {
    const res = await fetch(`${BASE}/approval`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, action }),
    });
    return res.json();
}

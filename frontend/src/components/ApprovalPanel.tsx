import React, { useState } from "react";
import { submitApproval } from "@/services";
import type { ComplianceResult } from "@/services";

interface Props {
    sessionId: string;
    compliance: ComplianceResult;
    onResolved: (reply: string) => void;
}

const gradeStyle: Record<string, { color: string; label: string; bg: string }> = {
    pass: { color: "#52c41a", label: "✅ 通过", bg: "#f6ffed" },
    warn: { color: "#faad14", label: "⚠️ 警示", bg: "#fffbe6" },
    block: { color: "#ff4d4f", label: "⛔ 拦截", bg: "#fff2f0" },
};

const ApprovalPanel: React.FC<Props> = ({ sessionId, compliance, onResolved }) => {
    const [loading, setLoading] = useState(false);
    const gs = gradeStyle[compliance.grade] || gradeStyle.block;

    const handleAction = async (action: "approve" | "reject") => {
        setLoading(true);
        try {
            const result = await submitApproval({ session_id: sessionId, action });
            onResolved(result.reply);
        } catch (err) {
            console.error("审批失败:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div
            style={{
                margin: "10px 0 20px 60px",
                padding: 16,
                borderRadius: 8,
                border: `2px solid ${gs.color}`,
                background: gs.bg,
            }}
        >
            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 12, color: gs.color }}>
                {gs.label} — 合规审查
            </div>

            {compliance.checks.map((check, i) => (
                <div
                    key={i}
                    style={{
                        fontSize: 13,
                        marginBottom: 6,
                        color: check.passed ? "#52c41a" : "#ff4d4f",
                    }}
                >
                    {check.passed ? "✅" : "❌"} {check.name}：{check.detail}
                </div>
            ))}

            <div style={{ marginTop: 14, display: "flex", gap: 10 }}>
                {compliance.grade !== "block" && (
                    <button
                        onClick={() => handleAction("approve")}
                        disabled={loading}
                        style={{
                            padding: "6px 16px",
                            background: "#1677ff",
                            color: "#fff",
                            border: "none",
                            borderRadius: 6,
                            cursor: loading ? "not-allowed" : "pointer",
                            fontSize: 13,
                        }}
                    >
                        {loading ? "处理中..." : "✅ 人工放行"}
                    </button>
                )}
                <button
                    onClick={() => handleAction("reject")}
                    disabled={loading}
                    style={{
                        padding: "6px 16px",
                        background: "#fff",
                        color: "#ff4d4f",
                        border: "1px solid #ff4d4f",
                        borderRadius: 6,
                        cursor: loading ? "not-allowed" : "pointer",
                        fontSize: 13,
                    }}
                >
                    {loading ? "处理中..." : "❌ 驳回"}
                </button>
            </div>
        </div>
    );
};

export default ApprovalPanel;

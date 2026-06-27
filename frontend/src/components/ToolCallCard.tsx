import React, { useState } from "react";
import { Card, Tag, Collapse, Spin, Typography } from "antd";
import {
    LoadingOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ToolOutlined,
} from "@ant-design/icons";

const { Text, Paragraph } = Typography;

interface ToolCallRecord {
    id: number;
    tool: string;
    args: unknown;
    result?: unknown;
    status: "running" | "done" | "error";
    error?: string;
}

const TOOL_LABELS: Record<string, string> = {
    get_fund_info: "📊 基金信息查询",
    get_fund_nav_history: "📈 净值历史",
    get_fund_holdings: "🏢 持仓查询",
    get_fund_risk_metrics: "⚠️ 风险指标",
    query_funds: "🔍 基金搜索",
    compare_funds: "📋 基金对比",
};

// 格式化值，支持嵌套对象/数组
function formatValue(val: unknown): string {
    if (val === null || val === undefined) return "—";
    if (typeof val === "object") {
        try { return JSON.stringify(val, null, 2); } catch { return String(val); }
    }
    return String(val);
}

const ToolCallCard: React.FC<{ toolCall: ToolCallRecord }> = ({ toolCall }) => {
    const [expanded, setExpanded] = useState(false);
    const label = TOOL_LABELS[toolCall.tool] || toolCall.tool;

    const statusIcon =
        toolCall.status === "running" ? (
            <Spin indicator={<LoadingOutlined spin />} size="small" />
        ) : toolCall.status === "error" ? (
            <CloseCircleOutlined style={{ color: "#ff4d4f" }} />
        ) : (
            <CheckCircleOutlined style={{ color: "#52c41a" }} />
        );

    return (
        <Card
            size="small"
            style={{
                margin: "8px 0",
                background: toolCall.status === "running" ? "#fafafa" : "#f6ffed",
                borderLeft: `3px solid ${toolCall.status === "running" ? "#1677ff" :
                        toolCall.status === "error" ? "#ff4d4f" : "#52c41a"
                    }`,
            }}
            onClick={() => toolCall.status !== "running" && setExpanded(!expanded)}
        >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {statusIcon}
                <Text strong>{label}</Text>
                {toolCall.status === "running" && (
                    <Tag color="processing">执行中</Tag>
                )}
                {toolCall.status === "done" && (
                    <Tag color="success" style={{ cursor: "pointer" }}>
                        {expanded ? "收起" : "展开结果 ▼"}
                    </Tag>
                )}
                {toolCall.status === "error" && (
                    <Tag color="error">失败</Tag>
                )}
            </div>

            {/* 调用参数 — 执行中时也显示 */}
            <div style={{ marginTop: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                    参数：<code>{JSON.stringify(toolCall.args)}</code>
                </Text>
            </div>

            {/* 返回结果 — 折叠面板 */}
            {toolCall.status !== "running" && expanded && (
                <div
                    style={{
                        marginTop: 8,
                        padding: 8,
                        background: "#fff",
                        border: "1px solid #f0f0f0",
                        borderRadius: 4,
                        maxHeight: 200,
                        overflow: "auto",
                    }}
                >
                    {toolCall.status === "error" ? (
                        <Text type="danger">{toolCall.error}</Text>
                    ) : (
                        <pre style={{ margin: 0, fontSize: 12, whiteSpace: "pre-wrap" }}>
                            {formatValue(toolCall.result)}
                        </pre>
                    )}
                </div>
            )}
        </Card>
    );
};

export default ToolCallCard;

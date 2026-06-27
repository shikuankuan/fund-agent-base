import React, { useState } from "react";
import { LoadingOutlined, CheckCircleOutlined, CaretDownOutlined, CaretRightOutlined } from "@ant-design/icons";
import { Tag, Typography } from "antd";

const { Text } = Typography;

// ===== 节点摘要类型（与后端 node_end payload 对齐） =====
export interface NodeSummary {
    node: string;
    label: string;
    status: "active" | "done";
    summary?: string;
    tools?: string[];
    grade?: string;
    fund_count?: number;
    route?: string;
    nextNode?: string;
    reasoning?: string;  // 推理过程（Reasoning Trace）
}

// ===== 工具名 → 中文标签 =====
const TOOL_LABELS: Record<string, string> = {
    get_fund_info: "基金信息",
    get_fund_nav: "净值查询",
    search_funds: "基金搜索",
    get_fund_manager_info: "经理查询",
    analyze_fund_performance: "业绩分析",
    analyze_fund_risk: "风险分析",
    compare_funds: "基金对比",
    check_risk_match: "风险匹配",
    check_compliance: "合规检查",
    risk_disclosure: "风险披露",
};

// ===== 合规等级颜色 =====
const GRADE_CONFIG: Record<string, { label: string; color: string }> = {
    pass: { label: "✅ 通过", color: "#52c41a" },
    warn: { label: "⚠️ 警告", color: "#faad14" },
    block: { label: "🚫 阻止", color: "#ff4d4f" },
};

// ===== 单个节点行 + 可展开推理 =====
const NodeRow: React.FC<{ n: NodeSummary }> = ({ n }) => {
    const [expanded, setExpanded] = useState(false);
    const hasReasoning = n.status === "done" && n.reasoning && n.reasoning.trim();

    return (
        <>
            {/* 节点行 */}
            <div
                style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 10,
                    padding: "4px 0",
                    fontSize: 13,
                    opacity: n.status === "active" ? 1 : 0.8,
                    transition: "opacity 0.3s",
                    cursor: hasReasoning ? "pointer" : "default",
                }}
                onClick={() => hasReasoning && setExpanded(!expanded)}
            >
                {/* 状态图标 */}
                <span
                    style={{
                        width: 16,
                        textAlign: "center",
                        flexShrink: 0,
                        marginTop: 1,
                    }}
                >
                    {n.status === "active" ? (
                        <LoadingOutlined spin style={{ fontSize: 13, color: "#1677ff" }} />
                    ) : (
                        <CheckCircleOutlined style={{ fontSize: 13, color: "#52c41a" }} />
                    )}
                </span>

                {/* 节点名 + 展开箭头 */}
                <Text
                    strong
                    style={{
                        minWidth: 56,
                        fontSize: 12,
                        flexShrink: 0,
                        color: n.status === "active" ? "#1677ff" : "#333",
                        display: "flex",
                        alignItems: "center",
                        gap: 3,
                    }}
                >
                    {n.label}
                    {hasReasoning && (
                        expanded
                            ? <CaretDownOutlined style={{ fontSize: 10, color: "#8c8c8c" }} />
                            : <CaretRightOutlined style={{ fontSize: 10, color: "#8c8c8c" }} />
                    )}
                </Text>

                {/* 右侧：工具标签 / 摘要文字 */}
                <div style={{ flex: 1, minWidth: 0 }}>
                    {n.status === "active" ? (
                        <Text type="secondary" style={{ fontSize: 11, color: "#1677ff" }}>
                            {n.summary || "执行中…"}
                        </Text>
                    ) : (
                        <>
                            {/* 工具标签（tool_selector） */}
                            {n.tools && n.tools.length > 0 && (
                                <span style={{ display: "inline-flex", gap: 4, flexWrap: "wrap" }}>
                                    {n.tools.map((t, i) => (
                                        <Tag
                                            key={i}
                                            style={{
                                                fontSize: 10,
                                                margin: 0,
                                                padding: "0 6px",
                                                lineHeight: "18px",
                                                borderRadius: 3,
                                            }}
                                        >
                                            {TOOL_LABELS[t] || t}
                                        </Tag>
                                    ))}
                                </span>
                            )}

                            {/* 合规审查等级 */}
                            {n.grade && GRADE_CONFIG[n.grade] && (
                                <Tag
                                    style={{
                                        fontSize: 10,
                                        margin: n.summary ? "0 0 0 6px" : 0,
                                        padding: "0 6px",
                                        lineHeight: "18px",
                                        borderRadius: 3,
                                        color: GRADE_CONFIG[n.grade].color,
                                        borderColor: GRADE_CONFIG[n.grade].color,
                                    }}
                                >
                                    {GRADE_CONFIG[n.grade].label}
                                </Tag>
                            )}

                            {/* 文字摘要 */}
                            {n.summary && !n.tools?.length && !n.grade && (
                                <Text
                                    type="secondary"
                                    style={{ fontSize: 11, lineHeight: "18px" }}
                                    ellipsis={{ tooltip: n.summary }}
                                >
                                    {n.summary}
                                </Text>
                            )}

                            {/* 缩略提示：推理可展开 */}
                            {hasReasoning && !expanded && (
                                <Text
                                    type="secondary"
                                    style={{
                                        fontSize: 9,
                                        marginLeft: 6,
                                        color: "#bfbfbf",
                                    }}
                                >
                                    💭
                                </Text>
                            )}

                            {/* 有工具/等级 + 有摘要 → 摘要放第二行 */}
                            {n.summary && (n.tools?.length || n.grade) && (
                                <Text
                                    type="secondary"
                                    style={{ fontSize: 10, display: "block", marginTop: 2 }}
                                >
                                    {n.summary}
                                </Text>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* 展开的推理过程 */}
            {hasReasoning && expanded && (
                <div
                    style={{
                        marginLeft: 26,
                        marginBottom: 2,
                        padding: "6px 10px",
                        background: "#f0f5ff",
                        borderRadius: 4,
                        borderLeft: "2px solid #1677ff",
                        whiteSpace: "pre-wrap",
                        fontSize: 11,
                        color: "#595959",
                        lineHeight: 1.6,
                    }}
                >
                    {n.reasoning}
                </div>
            )}
        </>
    );
};

// ===== 主组件 =====
interface AgentFlowProps {
    nodes: NodeSummary[];
}

const AgentFlow: React.FC<AgentFlowProps> = ({ nodes }) => {
    if (nodes.length === 0) return null;

    return (
        <div
            style={{
                marginBottom: 12,
                padding: "10px 14px",
                background: "linear-gradient(135deg, #f8fafd 0%, #f1f5ff 100%)",
                borderRadius: 8,
                border: "1px solid #e3ecfa",
            }}
        >
            <Text
                type="secondary"
                style={{
                    fontSize: 10,
                    marginBottom: 8,
                    display: "block",
                    letterSpacing: 1,
                    textTransform: "uppercase",
                }}
            >
                Agent 推理过程
            </Text>

            {nodes.map((n) => (
                <React.Fragment key={n.node}>
                    <NodeRow n={n} />

                    {/* 条件路由过渡线 */}
                    {n.status === "done" && n.route && (
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                padding: "2px 0 2px 7px",
                            }}
                        >
                            <span
                                style={{
                                    width: 1,
                                    height: 16,
                                    background: "#d9d9d9",
                                    marginRight: 10,
                                }}
                            />
                            <Text
                                type="secondary"
                                style={{
                                    fontSize: 10,
                                    color: "#8c8c8c",
                                    fontStyle: "italic",
                                }}
                            >
                                {n.route}
                            </Text>
                        </div>
                    )}
                </React.Fragment>
            ))}
        </div>
    );
};

export default AgentFlow;

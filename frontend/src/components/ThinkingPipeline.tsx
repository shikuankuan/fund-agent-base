import React from "react";

// ===== 节点配置 =====
interface PipelineNode {
    key: string;
    label: string;
    icon: string;
    status: "pending" | "active" | "done";
}

interface ThinkingPipelineProps {
    activeNode: string | null;
    completedNodes: Set<string>;
}

const NODE_CONFIG = [
    { key: "intent_recognizer", label: "意图识别", icon: "🔍" },
    { key: "tool_selector", label: "工具选择", icon: "🔧" },
    { key: "data_fetcher", label: "数据获取", icon: "📊" },
    { key: "analyzer", label: "分析计算", icon: "📈" },
    { key: "compliance_checker", label: "合规审查", icon: "⚖️" },
    { key: "response_generator", label: "生成回复", icon: "💬" },
];

const ThinkingPipeline: React.FC<ThinkingPipelineProps> = ({
    activeNode,
    completedNodes,
}) => {
    const nodes: PipelineNode[] = NODE_CONFIG.map((n) => ({
        ...n,
        status: completedNodes.has(n.key)
            ? "done"
            : n.key === activeNode
            ? "active"
            : "pending",
    }));

    const anyNodeActive = nodes.some((n) => n.status !== "pending");

    return (
        <div
            style={{
                background: "#fafbfc",
                borderRadius: 10,
                border: "1px solid #e8ecf1",
                padding: "14px 10px",
                marginBottom: 12,
                marginLeft: 56,
                marginRight: 56,
                position: "relative",
            }}
        >
            {/* 标题 */}
            <div
                style={{
                    fontSize: 11,
                    color: "#9ca3af",
                    marginBottom: 10,
                    textAlign: "center",
                    letterSpacing: 0.5,
                }}
            >
                {anyNodeActive ? "⚙️ Agent 执行流程" : "⏳ 等待响应..."}
            </div>

            {/* 管道 */}
            <div
                style={{
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "center",
                    gap: 0,
                    flexWrap: "wrap",
                }}
            >
                {nodes.map((node, i) => (
                    <React.Fragment key={node.key}>
                        {/* === 节点 === */}
                        <div
                            style={{
                                display: "flex",
                                flexDirection: "column",
                                alignItems: "center",
                                gap: 5,
                                minWidth: 64,
                                transition: "all 0.3s ease",
                            }}
                        >
                            {/* 圆形容器 */}
                            <div
                                style={{
                                    width: 38,
                                    height: 38,
                                    borderRadius: "50%",
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    fontSize: 16,
                                    lineHeight: 1,
                                    background:
                                        node.status === "done"
                                            ? "#52c41a"
                                            : node.status === "active"
                                            ? "#1677ff"
                                            : "#f0f0f0",
                                    color: node.status === "pending" ? "#bfbfbf" : "#fff",
                                    boxShadow:
                                        node.status === "active"
                                            ? "0 0 0 3px rgba(22,119,255,0.25)"
                                            : node.status === "done"
                                            ? "0 0 0 2px rgba(82,196,26,0.15)"
                                            : "none",
                                    animation:
                                        node.status === "active"
                                            ? "pipelinePulse 1.4s ease-in-out infinite"
                                            : "none",
                                    transition: "all 0.35s ease",
                                    position: "relative",
                                }}
                            >
                                {node.status === "done" ? (
                                    <span style={{ fontSize: 14, fontWeight: 700 }}>✓</span>
                                ) : (
                                    node.icon
                                )}

                                {/* 数据流波纹（active状态） */}
                                {node.status === "active" && (
                                    <>
                                        <div
                                            style={{
                                                position: "absolute",
                                                inset: -3,
                                                borderRadius: "50%",
                                                border: "1.5px solid #1677ff",
                                                opacity: 0.4,
                                                animation: "pipelineRipple 1.4s ease-out infinite",
                                            }}
                                        />
                                        <div
                                            style={{
                                                position: "absolute",
                                                inset: -6,
                                                borderRadius: "50%",
                                                border: "1px solid #1677ff",
                                                opacity: 0.2,
                                                animation: "pipelineRipple 1.4s ease-out 0.3s infinite",
                                            }}
                                        />
                                    </>
                                )}
                            </div>

                            {/* 标签 */}
                            <span
                                style={{
                                    fontSize: 11,
                                    fontWeight: node.status === "active" ? 600 : 400,
                                    color:
                                        node.status === "pending"
                                            ? "#bfbfbf"
                                            : node.status === "active"
                                            ? "#1677ff"
                                            : "#389e0d",
                                    whiteSpace: "nowrap",
                                    transition: "color 0.3s ease",
                                }}
                            >
                                {node.label}
                                {node.status === "active" && (
                                    <span
                                        style={{
                                            display: "inline-block",
                                            marginLeft: 2,
                                            animation: "pipelineDots 1s steps(3,end) infinite",
                                        }}
                                    >
                                        ...
                                    </span>
                                )}
                            </span>
                        </div>

                        {/* === 连接线（最后一个节点之后不渲染）=== */}
                        {i < nodes.length - 1 && (
                            <div
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                    alignItems: "center",
                                    minWidth: 20,
                                    marginTop: 18,
                                }}
                            >
                                {/* 线段 */}
                                <div
                                    style={{
                                        width: 20,
                                        height: 2,
                                        borderRadius: 1,
                                        background:
                                            node.status === "done" &&
                                            nodes[i + 1].status !== "pending"
                                                ? "#52c41a"
                                                : node.status === "done"
                                                ? "linear-gradient(90deg, #52c41a 50%, #e8ecf1 50%)"
                                                : "#e8ecf1",
                                        transition: "background 0.4s ease",
                                    }}
                                />
                                {/* 箭头尖 */}
                                <div
                                    style={{
                                        width: 0,
                                        height: 0,
                                        borderLeft: "5px solid transparent",
                                        borderRight: "5px solid transparent",
                                        borderBottom: `6px solid ${
                                            node.status === "done" &&
                                            nodes[i + 1].status !== "pending"
                                                ? "#52c41a"
                                                : node.status === "done"
                                                ? "#52c41a"
                                                : "#d9d9d9"
                                        }`,
                                        transform: "rotate(90deg)",
                                        marginTop: -5,
                                        marginLeft: 6,
                                        transition: "border-color 0.4s ease",
                                    }}
                                />
                            </div>
                        )}
                    </React.Fragment>
                ))}
            </div>

            {/* CSS 动画 */}
            <style>{`
                @keyframes pipelinePulse {
                    0%, 100% { box-shadow: 0 0 0 3px rgba(22,119,255,0.25); transform: scale(1); }
                    50% { box-shadow: 0 0 0 7px rgba(22,119,255,0.08); transform: scale(1.05); }
                }
                @keyframes pipelineRipple {
                    0% { transform: scale(1); opacity: 0.4; }
                    100% { transform: scale(1.4); opacity: 0; }
                }
                @keyframes pipelineDots {
                    0% { opacity: 0; }
                    33% { opacity: 1; }
                    66% { opacity: 1; }
                    100% { opacity: 0; }
                }
            `}</style>
        </div>
    );
};

export { NODE_CONFIG };
export default ThinkingPipeline;

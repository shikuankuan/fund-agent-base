import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github.css";
import { Table } from "antd";
import type { TableColumnsType } from "antd";
import FundNavCard from "./FundNavCard";
import FundHoldingsCard from "./FundHoldingsCard";
import FundRiskCard from "./FundRiskCard";
import FundInfoCard from "./FundInfoCard";
import FundCompareCard from "./FundCompareCard";

interface Props {
    content: string;
}

// ── 递归提取 React 节点的纯文本 ──
function extractText(node: React.ReactNode): string {
    if (typeof node === "string" || typeof node === "number") return String(node);
    if (Array.isArray(node)) return node.map(extractText).join("");
    if (React.isValidElement(node)) {
        return extractText((node.props as any).children);
    }
    return "";
}

// ── markdown 表格 → antd Table ──
const AntTable: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const cols: string[] = [];
    const rows: string[][] = [];

    // 过滤掉空白文本节点（markdown 解析产生的换行符会变成 <tr> 内的文本节点 → React 报错）
    const elements = React.Children.toArray(children).filter(
        (c) => React.isValidElement(c) || (typeof c === "string" && c.trim() !== "")
    );

    elements.forEach((child) => {
        if (!React.isValidElement(child)) return;
        const childType = child.type;
        if (childType === "thead") {
            const trChildren = React.Children.toArray(child.props.children).filter(
                (c: any) => React.isValidElement(c)
            );
            const firstRow = trChildren[0];
            if (React.isValidElement(firstRow)) {
                React.Children.forEach(firstRow.props.children, (th: any) => {
                    if (React.isValidElement(th) || typeof th === "string") {
                        cols.push(extractText(th));
                    }
                });
            }
        }
        if (childType === "tbody") {
            const trElements = React.Children.toArray(child.props.children).filter(
                (c: any) => React.isValidElement(c)
            );
            trElements.forEach((tr: any) => {
                if (!React.isValidElement(tr)) return;
                const row: string[] = [];
                React.Children.forEach(tr.props.children, (td: any) => {
                    if (React.isValidElement(td) || typeof td === "string") {
                        row.push(extractText(td));
                    }
                });
                rows.push(row);
            });
        }
    });

    if (cols.length === 0 || rows.length === 0) {
        return (
            <div style={{ overflowX: "auto", margin: "12px 0" }}>
                <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 13 }}>
                    {elements}
                </table>
            </div>
        );
    }

    const columns: TableColumnsType = cols.map((col, i) => ({
        title: col,
        dataIndex: `col_${i}`,
        key: `col_${i}`,
        ellipsis: true,
    }));

    const dataSource = rows.map((row, i) => {
        const record: Record<string, string> = { key: `row_${i}` };
        row.forEach((cell, j) => {
            record[`col_${j}`] = cell;
        });
        return record;
    });

    return (
        <div style={{ margin: "12px 0", maxWidth: "100%" }}>
            <Table
                columns={columns}
                dataSource={dataSource}
                pagination={false}
                size="small"
                bordered
                scroll={{ x: "max-content" }}
            />
        </div>
    );
};

// ── 卡片标签解析 ──
// 正则：<fund-NAME-card code="XXXXXX"/>  或  codes="000001,005827"
const CARD_TAG_RE = /<fund-(nav|info|holdings|risk|compare)-card\s+(code|codes)="([^"]+)"\s*\/>/g;

interface CardSegment {
    type: "text" | "card";
    content: string;
    cardType?: string;
    codes?: string[];
}

/** 把原始 Markdown 按卡片标签切成 text + card 交替数组 */
function parseContent(raw: string): CardSegment[] {
    const segments: CardSegment[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = CARD_TAG_RE.exec(raw)) !== null) {
        // 标签前的文字
        if (match.index > lastIndex) {
            segments.push({
                type: "text",
                content: raw.slice(lastIndex, match.index),
            });
        }
        // 卡片
        segments.push({
            type: "card",
            content: match[0],
            cardType: match[1],            // nav / info / holdings / risk / compare
            codes: match[3].split(",").map((s) => s.trim()),
        });
        lastIndex = match.index + match[0].length;
    }

    // 尾部文字
    if (lastIndex < raw.length) {
        segments.push({ type: "text", content: raw.slice(lastIndex) });
    }

    return segments;
}

// ── 卡片渲染映射 ──
function renderCard(seg: CardSegment): React.ReactNode {
    if (!seg.codes || seg.codes.length === 0) return null;
    const code = seg.codes[0];

    switch (seg.cardType) {
        case "nav":
            return <FundNavCard fundCode={code} />;
        case "holdings":
            return <FundHoldingsCard fundCode={code} />;
        case "risk":
            return <FundRiskCard fundCode={code} />;
        case "info":
            return <FundInfoCard fundCode={code} />;
        case "compare":
            return <FundCompareCard codes={seg.codes.join(",")} />;

        default:
            return null;
    }
}

// ── 通用 markdown 组件 ──
const markdownComponents = {
    table: ({ children }: any) => <AntTable>{children}</AntTable>,
    th: ({ children }: any) => <>{children}</>,
    td: ({ children }: any) => <>{children}</>,
    code: ({ className, children, ...props }: any) => {
        const isInline = !className;
        if (isInline) {
            return (
                <code
                    {...props}
                    style={{
                        background: "#f5f5f5",
                        padding: "2px 6px",
                        borderRadius: 4,
                        fontSize: "0.9em",
                        color: "#cf1322",
                    }}
                >
                    {children}
                </code>
            );
        }
        return (
            <code className={className} {...props}>
                {children}
            </code>
        );
    },
    a: ({ children, href, ...props }: any) => (
        <a href={href} target="_blank" rel="noopener noreferrer" {...props} style={{ color: "#1677ff" }}>
            {children}
        </a>
    ),
    hr: (props: any) => (
        <hr {...props} style={{ border: "none", borderTop: "1px solid #e8ecf1", margin: "16px 0" }} />
    ),
    ul: ({ children, ...props }: any) => (
        <ul {...props} style={{ paddingLeft: 20, margin: "8px 0" }}>
            {children}
        </ul>
    ),
    ol: ({ children, ...props }: any) => (
        <ol {...props} style={{ paddingLeft: 20, margin: "8px 0" }}>
            {children}
        </ol>
    ),
    li: ({ children, ...props }: any) => (
        <li {...props} style={{ marginBottom: 4 }}>
            {children}
        </li>
    ),
    blockquote: ({ children, ...props }: any) => (
        <blockquote
            {...props}
            style={{
                borderLeft: "3px solid #1677ff",
                paddingLeft: 12,
                margin: "8px 0",
                color: "#6b7280",
                background: "#f0f5ff",
                borderRadius: "0 4px 4px 0",
                padding: "8px 12px",
            }}
        >
            {children}
        </blockquote>
    ),
};

// ── 主组件 ──
const MarkdownRenderer: React.FC<Props> = ({ content }) => {
    const components = useMemo(() => markdownComponents, []);

    // 1. 解析卡片标签
    const segments = useMemo(() => parseContent(content), [content]);

    return (
        <div>
            {segments.map((seg, i) => {
                if (seg.type === "card") {
                    return <div key={`card-${i}`}>{renderCard(seg)}</div>;
                }
                // 跳过纯空白的 text 段
                if (!seg.content.trim()) return null;

                return (
                    <ReactMarkdown
                        key={`md-${i}`}
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeHighlight]}
                        components={components}
                    >
                        {seg.content}
                    </ReactMarkdown>
                );
            })}
        </div>
    );
};

export default MarkdownRenderer;

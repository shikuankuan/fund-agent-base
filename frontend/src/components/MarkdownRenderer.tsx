import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github.css";
import { Table } from "antd";
import type { TableColumnsType } from "antd";

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

    React.Children.forEach(children, (child) => {
        if (!React.isValidElement(child)) return;
        const childType = child.type;                    // ✅ 直接比较,HTML 元素的 type 是字符串
        if (childType === "thead") {
            const firstRow = React.Children.toArray(child.props.children)[0];
            if (React.isValidElement(firstRow)) {
                React.Children.forEach(firstRow.props.children, (th: any) => {
                    cols.push(extractText(th));
                });
            }
        }
        if (childType === "tbody") {
            React.Children.forEach(child.props.children, (tr: any) => {
                if (!React.isValidElement(tr)) return;
                const row: string[] = [];
                React.Children.forEach(tr.props.children, (td: any) => {
                    row.push(extractText(td));
                });
                rows.push(row);
            });
        }
    });

    if (cols.length === 0 || rows.length === 0) {
        return (
            <div style={{ overflowX: "auto", margin: "12px 0" }}>
                <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 13 }}>
                    {children}
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

const MarkdownRenderer: React.FC<Props> = ({ content }) => {
    const components = useMemo(
        () => ({
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
                <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    {...props}
                    style={{ color: "#1677ff" }}
                >
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
        }),
        [],
    );

    return (
        <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={components}
        >
            {content}
        </ReactMarkdown>
    );
};

export default MarkdownRenderer;

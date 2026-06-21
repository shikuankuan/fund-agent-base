import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github.css";

interface Props {
    content: string;
}

const MarkdownRenderer: React.FC<Props> = ({ content }) => {
    const components = useMemo(
        () => ({
            table: ({ children, ...props }: any) => (
                <div style={{ overflowX: "auto", margin: "12px 0" }}>
                    <table
                        {...props}
                        style={{
                            borderCollapse: "collapse",
                            width: "100%",
                            fontSize: 13,
                        }}
                    >
                        {children}
                    </table>
                </div>
            ),
            th: ({ children, ...props }: any) => (
                <th
                    {...props}
                    style={{
                        border: "1px solid #e8ecf1",
                        padding: "8px 12px",
                        background: "#f0f5ff",
                        fontWeight: 600,
                        textAlign: "left",
                        whiteSpace: "nowrap",
                    }}
                >
                    {children}
                </th>
            ),
            td: ({ children, ...props }: any) => (
                <td
                    {...props}
                    style={{
                        border: "1px solid #e8ecf1",
                        padding: "6px 12px",
                        fontSize: 13,
                    }}
                >
                    {children}
                </td>
            ),
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

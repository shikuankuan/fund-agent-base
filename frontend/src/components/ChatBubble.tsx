import React from "react";
import { Avatar, Typography } from "antd";
import { UserOutlined, RobotOutlined } from "@ant-design/icons";
import MarkdownRenderer from "./MarkdownRenderer";

const { Text } = Typography;

interface ChatBubbleProps {
    role: "user" | "assistant";
    content: string;
    timestamp?: string;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ role, content, timestamp }) => {
    const isUser = role === "user";

    return (
        <div
            style={{
                display: "flex",
                flexDirection: isUser ? "row-reverse" : "row",
                gap: 10,
                marginBottom: 20,
                padding: isUser ? "0 0 0 60px" : "0 60px 0 0",
            }}
        >
            <Avatar
                size={36}
                icon={isUser ? <UserOutlined /> : <RobotOutlined />}
                style={{
                    flexShrink: 0,
                    background: isUser
                        ? "linear-gradient(135deg, #1677ff, #69b1ff)"
                        : "linear-gradient(135deg, #52c41a, #95de64)",
                }}
            />

            <div style={{ maxWidth: "100%", minWidth: 0 }}>
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        marginBottom: 4,
                        paddingLeft: isUser ? 0 : 4,
                        paddingRight: isUser ? 4 : 0,
                        flexDirection: isUser ? "row-reverse" : "row",
                    }}
                >
                    <Text strong style={{ fontSize: 12 }}>
                        {isUser ? "我" : "基金助手"}
                    </Text>
                    {timestamp && (
                        <Text type="secondary" style={{ fontSize: 11 }}>
                            {timestamp}
                        </Text>
                    )}
                </div>

                <div
                    style={{
                        padding: "12px 16px",
                        borderRadius: isUser ? "12px 4px 12px 12px" : "4px 12px 12px 12px",
                        background: isUser ? "#1677ff" : "#ffffff",
                        color: isUser ? "#fff" : "#1f2937",
                        boxShadow: isUser ? "none" : "0 1px 3px rgba(0,0,0,0.08)",
                        border: isUser ? "none" : "1px solid #e8ecf1",
                        lineHeight: 1.7,
                        fontSize: 14,
                        wordBreak: "break-word",
                    }}
                >
                    {isUser ? (
                        <span style={{ whiteSpace: "pre-wrap" }}>{content}</span>
                    ) : (
                        <MarkdownRenderer content={content} />
                    )}
                </div>
            </div>
        </div>
    );
};

export default ChatBubble;

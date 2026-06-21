import React, { useState, KeyboardEvent } from "react";
import { Input, Button, Tag } from "antd";
import { SendOutlined, ThunderboltOutlined } from "@ant-design/icons";

const { TextArea } = Input;

const QUICK_QUESTIONS = [
    { label: "查净值", text: "帮我查一下000001的最新净值" },
    { label: "分析风险", text: "分析一下000001的投资风险" },
    { label: "基金对比", text: "帮我对比000001和005827" },
];

interface ChatInputProps {
    onSend: (message: string) => void;
    disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled }) => {
    const [text, setText] = useState("");

    const handleSend = () => {
        const trimmed = text.trim();
        if (!trimmed || disabled) return;
        onSend(trimmed);
        setText("");
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div style={{ borderTop: "1px solid #e8ecf1", background: "#fff", flexShrink: 0 }}>
            <div style={{ padding: "8px 20px 0", display: "flex", gap: 8, flexWrap: "wrap" }}>
                {QUICK_QUESTIONS.map((q) => (
                    <Tag
                        key={q.label}
                        style={{
                            cursor: disabled ? "not-allowed" : "pointer",
                            padding: "2px 10px",
                            borderRadius: 12,
                            fontSize: 12,
                            border: "1px solid #d9d9d9",
                            background: "#fafafa",
                            opacity: disabled ? 0.5 : 1,
                        }}
                        onClick={() => !disabled && onSend(q.text)}
                    >
                        <ThunderboltOutlined style={{ marginRight: 4 }} />
                        {q.label}
                    </Tag>
                ))}
            </div>

            <div style={{ display: "flex", alignItems: "flex-end", gap: 10, padding: "10px 20px 14px" }}>
                <TextArea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="输入消息（Enter 发送，Shift+Enter 换行）"
                    disabled={disabled}
                    autoSize={{ minRows: 1, maxRows: 4 }}
                    style={{ flex: 1, borderRadius: 8, fontSize: 14, resize: "none" }}
                />
                <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSend}
                    disabled={disabled || !text.trim()}
                    style={{ height: 38, width: 38, borderRadius: 8, flexShrink: 0 }}
                />
            </div>
        </div>
    );
};

export default ChatInput;

import React from "react";
import {
    Layout,
    Menu,
    Input,
    Button,
    Avatar,
    Badge,
    Typography,
    Tooltip,
} from "antd";
import {
    PlusOutlined,
    SearchOutlined,
    MessageOutlined,
    FundOutlined,
    SettingOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
} from "@ant-design/icons";
import type { MenuProps } from "antd";

const { Sider } = Layout;
const { Text } = Typography;

// ===== 模拟会话数据 =====
interface Session {
    id: string;
    title: string;
    lastMessage: string;
    time: string;
    unread?: number;
}

const mockSessions: Session[] = [
    {
        id: "1",
        title: "宽宽成长混合分析",
        lastMessage: "该基金近一年收益率15%，属于中高风险...",
        time: "10:32",
    },
    {
        id: "2",
        title: "R3 投资者合规咨询",
        lastMessage: "经评估，您的风险等级为R3，该基金为R4...",
        time: "昨天",
    },
    {
        id: "3",
        title: "易方达蓝筹精选对比",
        lastMessage: "两只基金近三年走势对比如下...",
        time: "周一",
        unread: 2,
    },
    {
        id: "4",
        title: "基金定投方案咨询",
        lastMessage: "建议采用周定投策略...",
        time: "上周五",
    },
];

// ===== Props =====
interface SidebarProps {
    collapsed: boolean;
    onCollapse: (v: boolean) => void;
    activeSession: string;
    onSessionChange: (id: string) => void;
    onNewSession: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
    collapsed,
    onCollapse,
    activeSession,
    onSessionChange,
    onNewSession,
}) => {
    // ---------- 菜单项 ----------
    const menuItems: MenuProps["items"] = [
        {
            key: "g1",
            type: "group",
            label: collapsed ? "" : "会话列表",
            children: mockSessions.map((s) => ({
                key: s.id,
                icon: <MessageOutlined />,
                label: collapsed ? (
                    <Tooltip title={s.title} placement="right">
                        <span>{s.title.slice(0, 4)}...</span>
                    </Tooltip>
                ) : (
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            width: "100%",
                            overflow: "hidden",
                        }}
                    >
                        <span
                            style={{
                                flex: 1,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                            }}
                        >
                            {s.title}
                        </span>
                        {s.unread ? (
                            <Badge
                                count={s.unread}
                                size="small"
                                style={{ marginLeft: 4 }}
                            />
                        ) : null}
                    </div>
                ),
            })),
        },
    ];

    // ---------- 底部菜单 ----------
    const bottomItems: MenuProps["items"] = [
        {
            key: "settings",
            icon: <SettingOutlined />,
            label: collapsed ? "" : "设置",
        },
    ];

    return (
        <Sider
            width={260}
            collapsedWidth={64}
            collapsible
            collapsed={collapsed}
            onCollapse={onCollapse}
            trigger={null}
            style={{
                height: "100vh",
                borderRight: "1px solid rgba(255,255,255,0.06)",
            }}
        >
            {/* ---- Logo 区 ---- */}
            <div
                style={{
                    height: 56,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: collapsed ? "center" : "space-between",
                    padding: collapsed ? 0 : "0 16px",
                    borderBottom: "1px solid rgba(255,255,255,0.06)",
                }}
            >
                {!collapsed && (
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <Avatar
                            size={32}
                            icon={<FundOutlined />}
                            style={{ background: "linear-gradient(135deg, #1677ff, #69b1ff)" }}
                        />
                        <div>
                            <div style={{ color: "#fff", fontWeight: 600, fontSize: 14, lineHeight: 1.2 }}>
                                基金智能助手
                            </div>
                            <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 11 }}>
                                Fund Agent v1.0
                            </div>
                        </div>
                    </div>
                )}
                <Button
                    type="text"
                    icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                    onClick={() => onCollapse(!collapsed)}
                    style={{ color: "rgba(255,255,255,0.65)" }}
                />
            </div>

            {/* ---- 新建会话 ---- */}
            {!collapsed && (
                <div style={{ padding: "12px 16px" }}>
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        block
                        onClick={onNewSession}
                        style={{
                            height: 38,
                            borderRadius: 8,
                            fontWeight: 500,
                        }}
                    >
                        新建会话
                    </Button>
                </div>
            )}
            {collapsed && (
                <div style={{ padding: "8px", textAlign: "center" }}>
                    <Tooltip title="新建会话" placement="right">
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            shape="circle"
                            size="small"
                            onClick={onNewSession}
                        />
                    </Tooltip>
                </div>
            )}

            {/* ---- 搜索 ---- */}
            {!collapsed && (
                <div style={{ padding: "0 16px 8px" }}>
                    <Input
                        prefix={<SearchOutlined style={{ color: "rgba(255,255,255,0.3)" }} />}
                        placeholder="搜索会话..."
                        variant="borderless"
                        style={{
                            background: "rgba(255,255,255,0.06)",
                            borderRadius: 8,
                            color: "#fff",
                            height: 36,
                        }}
                    />
                </div>
            )}

            {/* ---- 会话列表 ---- */}
            <div style={{ flex: 1, overflow: "auto" }}>
                <Menu
                    mode="inline"
                    selectedKeys={[activeSession]}
                    onClick={({ key }) => onSessionChange(key)}
                    items={menuItems}
                    style={{
                        background: "transparent",
                        borderInlineEnd: "none",
                    }}
                    theme="dark"
                />
            </div>

            {/* ---- 底部：用户信息 + 设置 ---- */}
            <div
                style={{
                    borderTop: "1px solid rgba(255,255,255,0.06)",
                    padding: collapsed ? "8px" : "12px 16px",
                }}
            >
                {/* 用户信息行 */}
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        marginBottom: collapsed ? 0 : 10,
                        justifyContent: collapsed ? "center" : "flex-start",
                    }}
                >
                    <Avatar
                        size={collapsed ? 28 : 36}
                        style={{ background: "#52c41a", flexShrink: 0 }}
                    >
                        {collapsed ? "S" : "石"}
                    </Avatar>
                    {!collapsed && (
                        <div style={{ flex: 1, overflow: "hidden" }}>
                            <Text
                                style={{ color: "#fff", fontSize: 13, display: "block" }}
                                ellipsis
                            >
                                石SKK
                            </Text>
                            <Text style={{ color: "rgba(255,255,255,0.45)", fontSize: 11 }}>
                                R3 · 稳健型
                            </Text>
                        </div>
                    )}
                </div>

                {/* 设置菜单 */}
                <Menu
                    mode="inline"
                    items={bottomItems}
                    selectable={false}
                    style={{
                        background: "transparent",
                        borderInlineEnd: "none",
                    }}
                    theme="dark"
                />
            </div>
        </Sider>
    );
};

export default Sidebar;


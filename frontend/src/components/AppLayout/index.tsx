import React, { useState, useCallback } from "react";
import { Layout, Grid, Drawer, FloatButton } from "antd";
import { MenuOutlined } from "@ant-design/icons";
import Sidebar from "@/components/Sidebar";
import FundPanel from "@/components/FundPanel";
import ChatPanel from "@/components/ChatPanel";

const { Content } = Layout;
const { useBreakpoint } = Grid;

const AppLayout: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);
    const [activeSession, setActiveSession] = useState("1");
    const [showFundPanel, setShowFundPanel] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const screens = useBreakpoint();
    const isDesktop = !!screens.xxl || !!screens.xl;
    const isTablet = !!screens.lg || !!screens.md;
    const isMobile = !isDesktop && !isTablet;

    const sidebarWidth = isMobile ? 0 : isTablet ? 64 : collapsed ? 64 : 260;
    const panelWidth = isDesktop && showFundPanel ? 320 : 0;

    const handleNewSession = useCallback(() => {
        const newId = `session-${Date.now()}`;
        setActiveSession(newId);
        if (isMobile) setMobileMenuOpen(false);
    }, [isMobile]);

    const handleSessionChange = useCallback(
        (id: string) => {
            setActiveSession(id);
            if (isMobile) setMobileMenuOpen(false);
        },
        [isMobile],
    );

    return (
        <div
            style={{
                paddingRight: panelWidth,
                transition: "padding 0.25s ease",
                height: "100vh",
                overflow: "hidden",
            }}
        >
            <Layout style={{ height: "100vh", position: "relative" }}>
                {/* ======== 侧边栏 ======== */}
                {isMobile ? (
                    <Drawer
                        open={mobileMenuOpen}
                        onClose={() => setMobileMenuOpen(false)}
                        placement="left"
                        width={260}
                        styles={{
                            body: { padding: 0, background: "var(--sidebar-bg)" },
                            header: { display: "none" },
                        }}
                    >
                        <Sidebar
                            collapsed={false}
                            onCollapse={() => setMobileMenuOpen(false)}
                            activeSession={activeSession}
                            onSessionChange={handleSessionChange}
                            onNewSession={handleNewSession}
                        />
                    </Drawer>
                ) : (
                    <Sidebar
                        collapsed={collapsed}
                        onCollapse={setCollapsed}
                        activeSession={activeSession}
                        onSessionChange={handleSessionChange}
                        onNewSession={handleNewSession}
                    />
                )}

                {/* ======== 主聊天区 ======== */}
                <Layout style={{ height: "100vh", background: "#f5f6f8" }}>
                    <Content
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            height: "100%",
                            position: "relative",
                        }}
                    >
                        {/* 顶部栏 */}
                        <div
                            style={{
                                height: 56,
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                padding: "0 20px",
                                background: "#fff",
                                borderBottom: "1px solid #e8ecf1",
                                flexShrink: 0,
                            }}
                        >
                            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                {isMobile && (
                                    <MenuOutlined
                                        style={{ fontSize: 18, cursor: "pointer" }}
                                        onClick={() => setMobileMenuOpen(true)}
                                    />
                                )}
                                <span style={{ fontWeight: 600, fontSize: 15 }}>
                                    基金智能助手
                                </span>
                            </div>

                            <button
                                onClick={() => setShowFundPanel(!showFundPanel)}
                                style={{
                                    padding: "4px 14px",
                                    background: showFundPanel ? "#e6f4ff" : "#fff",
                                    color: showFundPanel ? "#1677ff" : "#666",
                                    border: `1px solid ${showFundPanel ? "#1677ff" : "#d9d9d9"}`,
                                    borderRadius: 6,
                                    fontSize: 12,
                                    cursor: "pointer",
                                    fontWeight: 500,
                                }}
                            >
                                {showFundPanel ? "✓ 已展开" : "📊 基金详情"}
                            </button>
                        </div>

                        <ChatPanel activeSession={activeSession} />
                    </Content>
                </Layout>

                {/* ======== 基金详情面板 ======== */}
                {isDesktop ? (
                    <FundPanel
                        visible={showFundPanel}
                        onClose={() => setShowFundPanel(false)}
                    />
                ) : (
                    <Drawer
                        title={null}
                        open={showFundPanel}
                        onClose={() => setShowFundPanel(false)}
                        placement="right"
                        width={320}
                        styles={{ body: { padding: 0 } }}
                    >
                        <FundPanel
                            visible={true}
                            onClose={() => setShowFundPanel(false)}
                        />
                    </Drawer>
                )}

                {/* 手机浮动按钮 */}
                {isMobile && (
                    <FloatButton
                        icon={<MenuOutlined />}
                        onClick={() => setMobileMenuOpen(true)}
                        style={{ left: 16, bottom: 24 }}
                    />
                )}
            </Layout>
        </div>
    );
};

export default AppLayout;

import React from "react";
import {
    Card,
    Descriptions,
    Tag,
    Statistic,
    Progress,
    Typography,
    Button,
    Tooltip,
} from "antd";
import {
    RiseOutlined,
    FallOutlined,
    InfoCircleOutlined,
    CloseOutlined,
    ArrowUpOutlined,
    ArrowDownOutlined,
} from "@ant-design/icons";

const { Title, Text } = Typography;

// ===== 基金数据类型 =====
interface FundDetail {
    code: string;
    name: string;
    type: string;
    riskLevel: string;
    nav: number;
    navChange: number;
    navChangePercent: number;
    return1y: number;
    return3y: number;
    sharpe: number;
    maxDrawdown: number;
    volatility: number;
    manager: string;
    company: string;
    scale: string;
}

// ===== 模拟数据 =====
const mockFund: FundDetail = {
    code: "000001",
    name: "宽宽成长混合",
    type: "混合型",
    riskLevel: "R4",
    nav: 1.8523,
    navChange: 0.0125,
    navChangePercent: 0.68,
    return1y: 15.0,
    return3y: 45.0,
    sharpe: 1.2,
    maxDrawdown: 12.0,
    volatility: 18.0,
    manager: "王明",
    company: "宽宽基金管理有限公司",
    scale: "86.52亿",
};

// ===== Props =====
interface FundPanelProps {
    visible: boolean;
    onClose: () => void;
    fundData?: FundDetail;
}

const FundPanel: React.FC<FundPanelProps> = ({
    visible,
    onClose,
    fundData = mockFund,
}) => {
    if (!visible) return null;

    const isPositive = fundData.navChange >= 0;

    return (
        <div
            style={{
                width: 320,
                height: "100vh",
                position: "fixed",
                right: 0,
                top: 0,
                bottom: 0,
                background: "#fff",
                borderLeft: "1px solid var(--border-light, #e8ecf1)",
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)",
                overflow: "auto",
                zIndex: 90,
                display: "flex",
                flexDirection: "column",
            }}
        >
            {/* ---- 标题栏 ---- */}
            <div
                style={{
                    padding: "14px 16px",
                    borderBottom: "1px solid #e8ecf1",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    background: "linear-gradient(135deg, #f0f5ff, #e6f7ff)",
                }}
            >
                <div>
                    <Text type="secondary" style={{ fontSize: 11, display: "block", marginBottom: 2 }}>
                        基金详情
                    </Text>
                    <Title level={5} style={{ margin: 0, fontSize: 15 }}>
                        {fundData.name}
                    </Title>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                        {fundData.code} · {fundData.type}
                    </Text>
                </div>
                <Button
                    type="text"
                    size="small"
                    icon={<CloseOutlined />}
                    onClick={onClose}
                />
            </div>

            {/* ---- 内容区 ---- */}
            <div style={{ flex: 1, overflow: "auto", padding: 16 }}>
                {/* 净值卡片 */}
                <Card
                    size="small"
                    style={{ marginBottom: 12, borderRadius: 8 }}
                    styles={{ body: { padding: "14px 16px" } }}
                >
                    <Text type="secondary" style={{ fontSize: 12 }}>最新净值（单位：元）</Text>
                    <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginTop: 4 }}>
                        <span style={{ fontSize: 28, fontWeight: 700 }}>
                            {fundData.nav.toFixed(4)}
                        </span>
                        <span
                            style={{
                                fontSize: 14,
                                fontWeight: 500,
                                color: isPositive ? "#cf1322" : "#389e0d",
                            }}
                        >
                            {isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                            {fundData.navChangePercent > 0 ? "+" : ""}
                            {fundData.navChangePercent}%
                        </span>
                    </div>
                </Card>

                {/* 风险等级 */}
                <Card
                    size="small"
                    style={{ marginBottom: 12, borderRadius: 8 }}
                    styles={{ body: { padding: "14px 16px" } }}
                >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>风险等级</Text>
                        <Tag color="error" style={{ borderRadius: 4, fontWeight: 500 }}>
                            {fundData.riskLevel} · 中高风险
                        </Tag>
                    </div>
                </Card>

                {/* 收益表现 */}
                <Card
                    size="small"
                    title={<span style={{ fontSize: 13, fontWeight: 500 }}>收益表现</span>}
                    style={{ marginBottom: 12, borderRadius: 8 }}
                    styles={{ body: { padding: "8px 16px 14px" } }}
                >
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                        <Statistic
                            title="近一年"
                            value={fundData.return1y}
                            suffix="%"
                            valueStyle={{
                                fontSize: 20,
                                color: fundData.return1y >= 0 ? "#cf1322" : "#389e0d",
                            }}
                            prefix={fundData.return1y >= 0 ? <RiseOutlined /> : <FallOutlined />}
                        />
                        <Statistic
                            title="近三年"
                            value={fundData.return3y}
                            suffix="%"
                            valueStyle={{
                                fontSize: 20,
                                color: fundData.return3y >= 0 ? "#cf1322" : "#389e0d",
                            }}
                            prefix={fundData.return3y >= 0 ? <RiseOutlined /> : <FallOutlined />}
                        />
                    </div>
                </Card>

                {/* 风险指标 */}
                <Card
                    size="small"
                    title={<span style={{ fontSize: 13, fontWeight: 500 }}>风险指标</span>}
                    style={{ marginBottom: 12, borderRadius: 8 }}
                    styles={{ body: { padding: "10px 16px 14px" } }}
                >
                    {/* 最大回撤 */}
                    <div style={{ marginBottom: 14 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                            <Text style={{ fontSize: 12 }}>最大回撤</Text>
                            <Text style={{ fontSize: 12, color: "#ff4d4f" }}>-{fundData.maxDrawdown}%</Text>
                        </div>
                        <Progress
                            percent={fundData.maxDrawdown}
                            showInfo={false}
                            strokeColor={{ "0%": "#ff4d4f", "100%": "#ffa940" }}
                            trailColor="#f0f0f0"
                            size="small"
                        />
                    </div>
                    {/* 年化波动率 */}
                    <div style={{ marginBottom: 14 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                            <Text style={{ fontSize: 12 }}>年化波动率</Text>
                            <Text style={{ fontSize: 12 }}>{fundData.volatility}%</Text>
                        </div>
                        <Progress
                            percent={fundData.volatility}
                            showInfo={false}
                            strokeColor={{ "0%": "#faad14", "100%": "#ffc53d" }}
                            trailColor="#f0f0f0"
                            size="small"
                        />
                    </div>
                    {/* 夏普比率 */}
                    <div>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                            <Text style={{ fontSize: 12 }}>
                                夏普比率
                                <Tooltip title="衡量单位风险带来的超额回报，越高越好">
                                    <InfoCircleOutlined style={{ marginLeft: 4, color: "#999", fontSize: 11 }} />
                                </Tooltip>
                            </Text>
                            <Text
                                style={{
                                    fontSize: 12,
                                    fontWeight: 500,
                                    color: fundData.sharpe >= 1 ? "#52c41a" : "#faad14",
                                }}
                            >
                                {fundData.sharpe.toFixed(2)}
                            </Text>
                        </div>
                        <Progress
                            percent={(fundData.sharpe / 2) * 100}
                            showInfo={false}
                            strokeColor="#52c41a"
                            trailColor="#f0f0f0"
                            size="small"
                        />
                    </div>
                </Card>

                {/* 基本信息 */}
                <Card
                    size="small"
                    title={<span style={{ fontSize: 13, fontWeight: 500 }}>基本信息</span>}
                    style={{ borderRadius: 8 }}
                    styles={{ body: { padding: "4px 16px 10px" } }}
                >
                    <Descriptions
                        column={1}
                        size="small"
                        colon={false}
                        labelStyle={{ color: "#999", fontSize: 12, paddingBottom: 4 }}
                        contentStyle={{ fontSize: 13, paddingBottom: 4 }}
                    >
                        <Descriptions.Item label="基金经理">{fundData.manager}</Descriptions.Item>
                        <Descriptions.Item label="基金公司">{fundData.company}</Descriptions.Item>
                        <Descriptions.Item label="基金规模">{fundData.scale}</Descriptions.Item>
                    </Descriptions>
                </Card>
            </div>
        </div>
    );
};

export default FundPanel;

import React from "react";
import { Card, Descriptions, Tag, Typography } from "antd";
import {
    FundOutlined,
    BankOutlined,
    CalendarOutlined,
    TeamOutlined,
    SafetyCertificateOutlined,
} from "@ant-design/icons";

const { Text, Paragraph } = Typography;

// ════════════════════════════════════════
// 类型定义
// ════════════════════════════════════════

export interface FundInfoData {
    code: string;
    name: string;
    type: string;
    risk_level: string;
    company: string;
    scale: string;
    establish_date: string;
    custodian?: string;
    manager_name: string;
    manager_tenure_years: number;
    description?: string;
}

interface FundInfoCardProps {
    data: FundInfoData | null;
    loading?: boolean;
}

// ════════════════════════════════════════
// 风险等级颜色映射
// ════════════════════════════════════════

const RISK_COLOR_MAP: Record<string, string> = {
    "低风险": "#52c41a",
    "中低风险": "#73d13d",
    "中风险": "#faad14",
    "中高风险": "#ff7a45",
    "高风险": "#ff4d4f",
};

// 模糊匹配（因为数据里是"中风险"、"中高风险"这种中文标签）
function getRiskColor(level: string): string {
    for (const [key, color] of Object.entries(RISK_COLOR_MAP)) {
        if (level.includes(key)) return color;
    }
    return "#d9d9d9";
}

// ════════════════════════════════════════
// 组件
// ════════════════════════════════════════

const FundInfoCard: React.FC<FundInfoCardProps> = ({ data, loading }) => {
    // 空数据 & 非 loading 态 = 不渲染
    if (!data && !loading) return null;

    return (
        <Card
            loading={loading}
            size="small"
            style={{ borderRadius: 8, marginBottom: 12 }}
            styles={{ body: { padding: "12px 16px" } }}
            title={
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <FundOutlined style={{ color: "#1677ff" }} />
                    <Text strong style={{ fontSize: 15 }}>
                        {data?.name ?? "加载中…"}
                    </Text>
                    {data?.risk_level && (
                        <Tag color={getRiskColor(data.risk_level)} style={{ marginLeft: 4 }}>
                            <SafetyCertificateOutlined /> {data.risk_level}
                        </Tag>
                    )}
                </div>
            }
        >
            {/* ── 第一区：核心信息 ── */}
            <Descriptions column={2} size="small" colon={false}>
                <Descriptions.Item label={<Text type="secondary">基金代码</Text>}>
                    <Text code>{data?.code}</Text>
                </Descriptions.Item>
                <Descriptions.Item label={<Text type="secondary">基金类型</Text>}>
                    {data?.type}
                </Descriptions.Item>
                <Descriptions.Item
                    label={
                        <span>
                            <BankOutlined style={{ marginRight: 4 }} />
                            <Text type="secondary">基金公司</Text>
                        </span>
                    }
                >
                    {data?.company}
                </Descriptions.Item>
                <Descriptions.Item label={<Text type="secondary">规模</Text>}>
                    {data?.scale}
                </Descriptions.Item>
                <Descriptions.Item
                    label={
                        <span>
                            <CalendarOutlined style={{ marginRight: 4 }} />
                            <Text type="secondary">成立日期</Text>
                        </span>
                    }
                >
                    {data?.establish_date}
                </Descriptions.Item>
                <Descriptions.Item label={<Text type="secondary">托管银行</Text>}>
                    {data?.custodian ?? "—"}
                </Descriptions.Item>
                <Descriptions.Item
                    label={
                        <span>
                            <TeamOutlined style={{ marginRight: 4 }} />
                            <Text type="secondary">基金经理</Text>
                        </span>
                    }
                    span={2}
                >
                    {data?.manager_name}
                    {data?.manager_tenure_years != null && (
                        <Text type="secondary" style={{ marginLeft: 6 }}>
                            （任职 {data.manager_tenure_years} 年）
                        </Text>
                    )}
                </Descriptions.Item>
            </Descriptions>

            {/* ── 第二区：基金简介（有数据时才显示）── */}
            {data?.description && (
                <>
                    <div
                        style={{
                            marginTop: 12,
                            borderTop: "1px solid #f0f0f0",
                            paddingTop: 10,
                        }}
                    >
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            📝 基金简介
                        </Text>
                    </div>
                    <Paragraph
                        type="secondary"
                        style={{ fontSize: 13, marginBottom: 0, marginTop: 4 }}
                        ellipsis={{ rows: 2, expandable: true, symbol: "展开" }}
                    >
                        {data.description}
                    </Paragraph>
                </>
            )}
        </Card>
    );
};

export default FundInfoCard;

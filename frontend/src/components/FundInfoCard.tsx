import React, { useEffect, useState, useCallback } from "react";
import { Card, Spin, Empty, Typography, Tag, Descriptions, Statistic, Row, Col, Divider } from "antd";
import {
  RiseOutlined,
  FallOutlined,
  UserOutlined,
  BankOutlined,
  SafetyCertificateOutlined,
  CalendarOutlined,
  FundOutlined,
} from "@ant-design/icons";

const { Text, Paragraph } = Typography;

// ════════════════════════════════════════
// 类型
// ════════════════════════════════════════

interface FundInfoData {
  fund_code: string;
  fund_name: string;
  fund_type: string;
  risk_level: string;
  company: string;
  custodian: string;
  founded_date: string;
  scale: string;
  description: string;
  manager: {
    name: string;
    tenure_years: number;
    investment_style: string;
    current_funds: string[];
    historical_returns: Record<string, number>;
  };
  nav: {
    current: number;
    cumulative: number;
    daily_change: number;
    yearly_change: number;
  };
  risk_metrics: {
    sharpe_ratio: number;
    max_drawdown: number;
    volatility: number;
  };
}

interface Props {
  fundCode: string;
}

// ════════════════════════════════════════
// 风险等级配色
// ════════════════════════════════════════

const RISK_COLOR: Record<string, string> = {
  "低风险": "#52c41a",
  "中低风险": "#73d13d",
  "中风险": "#faad14",
  "中高风险": "#ff7a45",
  "高风险": "#ff4d4f",
};

// ════════════════════════════════════════
// 主组件
// ════════════════════════════════════════

const FundInfoCard: React.FC<Props> = ({ fundCode }) => {
  const [data, setData] = useState<FundInfoData | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/funds/${fundCode}/info`);
      const json = await res.json();
      if (json.code === 0) setData(json.data as FundInfoData);
    } catch (err) {
      console.error("[信息卡片] 请求失败", err);
    } finally {
      setLoading(false);
    }
  }, [fundCode]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (!data && !loading) return null;

  const riskColor = RISK_COLOR[data?.risk_level ?? ""] ?? "#faad14";
  const dailyUp = (data?.nav.daily_change ?? 0) >= 0;
  const yearlyUp = (data?.nav.yearly_change ?? 0) >= 0;

  return (
    <Card
      size="small"
      style={{ borderRadius: 8, marginBottom: 12 }}
      styles={{ body: { padding: "12px 16px" } }}
      title={
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 4 }}>
          <div>
            <Text strong style={{ fontSize: 14 }}>
              📋 {data?.fund_name ?? fundCode}
            </Text>
            <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
              {data?.fund_code}
            </Text>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <Tag color="blue">{data?.fund_type}</Tag>
            <Tag color={riskColor}>{data?.risk_level}</Tag>
          </div>
        </div>
      }
    >
      <Spin spinning={loading}>
        {data ? (
          <>
            {/* ── 一行：关键数字 ── */}
            <Row gutter={[12, 12]} style={{ marginBottom: 8 }}>
              <Col xs={12} sm={8} md={4}>
                <Statistic
                  title="最新净值"
                  value={data.nav.current}
                  precision={4}
                  valueStyle={{ fontSize: 20, fontWeight: 700 }}
                />
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Statistic
                  title="日涨跌"
                  value={data.nav.daily_change}
                  precision={2}
                  suffix="%"
                  prefix={dailyUp ? <RiseOutlined /> : <FallOutlined />}
                  valueStyle={{
                    fontSize: 18,
                    color: dailyUp ? "#cf1322" : "#3f8600",
                  }}
                />
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Statistic
                  title="年化收益"
                  value={data.nav.yearly_change}
                  precision={2}
                  suffix="%"
                  prefix={yearlyUp ? <RiseOutlined /> : <FallOutlined />}
                  valueStyle={{
                    fontSize: 18,
                    color: yearlyUp ? "#cf1322" : "#3f8600",
                  }}
                />
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Statistic
                  title="Sharpe"
                  value={data.risk_metrics.sharpe_ratio}
                  precision={2}
                  valueStyle={{ fontSize: 18 }}
                />
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Statistic
                  title="最大回撤"
                  value={data.risk_metrics.max_drawdown}
                  precision={2}
                  suffix="%"
                  valueStyle={{ fontSize: 18, color: "#ff4d4f" }}
                />
              </Col>
              <Col xs={12} sm={8} md={4}>
                <Statistic
                  title="累计净值"
                  value={data.nav.cumulative}
                  precision={4}
                  valueStyle={{ fontSize: 18 }}
                />
              </Col>
            </Row>

            {/* ── 基本信息 Descriptions ── */}
            <Descriptions
              size="small"
              column={{ xs: 1, sm: 2, md: 3 }}
              colon={false}
              style={{ marginBottom: 4 }}
            >
              <Descriptions.Item label={<><UserOutlined /> 基金经理</>}>
                <Text>
                  {data.manager.name}
                  <Text type="secondary" style={{ fontSize: 12, marginLeft: 4 }}>
                    （从业 {data.manager.tenure_years} 年）
                  </Text>
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label={<><BankOutlined /> 基金公司</>}>
                {data.company}
              </Descriptions.Item>
              <Descriptions.Item label={<><SafetyCertificateOutlined /> 托管银行</>}>
                {data.custodian}
              </Descriptions.Item>
              <Descriptions.Item label={<><CalendarOutlined /> 成立日期</>}>
                {data.founded_date}
              </Descriptions.Item>
              <Descriptions.Item label={<><FundOutlined /> 基金规模</>}>
                {data.scale}
              </Descriptions.Item>
              <Descriptions.Item label="投资风格">
                <Text>{data.manager.investment_style || "—"}</Text>
              </Descriptions.Item>
            </Descriptions>

            {/* ── 简介（可展开） ── */}
            <Divider style={{ margin: "8px 0" }} />
            <div
              style={{ cursor: "pointer" }}
              onClick={() => setExpanded(!expanded)}
            >
              <Text type="secondary" style={{ fontSize: 11 }}>
                {expanded ? "收起简介 ▲" : "展开简介 ▼"}
              </Text>
            </div>
            <Paragraph
              type="secondary"
              style={{
                marginTop: 4,
                marginBottom: 0,
                fontSize: 13,
                lineHeight: 1.6,
                maxHeight: expanded ? "none" : 44,
                overflow: "hidden",
                transition: "max-height 0.3s",
              }}
            >
              {data.description}
            </Paragraph>
          </>
        ) : (
          !loading && (
            <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Empty description="暂无基金信息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            </div>
          )
        )}
      </Spin>
    </Card>
  );
};

export default FundInfoCard;

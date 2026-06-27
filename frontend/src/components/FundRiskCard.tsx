import React, { useEffect, useState, useCallback } from "react";
import { Card, Spin, Empty, Typography, Row, Col, Tag } from "antd";
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip as ReTooltip,
} from "recharts";

const { Text } = Typography;

// ════════════════════════════════════════
// 类型
// ════════════════════════════════════════

interface RiskMetrics {
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  beta: number;
  alpha: number;
}

interface RiskData {
  fund_code: string;
  fund_name: string;
  risk_level: string;
  fund_type: string;
  metrics: RiskMetrics;
  returns: { monthly: number; yearly: number };
}

interface Props {
  fundCode: string;
}

// ════════════════════════════════════════
// 风险等级配色
// ════════════════════════════════════════

const RISK_COLORS: Record<string, string> = {
  "低风险": "#52c41a",
  "中低风险": "#73d13d",
  "中风险": "#faad14",
  "中高风险": "#ff7a45",
  "高风险": "#ff4d4f",
};

// ════════════════════════════════════════
// 指标归一化 → 0-100（雷达图需要统一量纲）
// ════════════════════════════════════════

function normalizeRadar(m: RiskMetrics, yReturn: number) {
  return [
    {
      metric: "Sharpe比率",
      value: Math.min(Math.max((m.sharpe_ratio / 3) * 100, 0), 100),
      raw: m.sharpe_ratio.toFixed(2),
      better: "high",
    },
    {
      metric: "抗回撤力",
      value: Math.min(Math.max((1 - Math.abs(m.max_drawdown) / 50) * 100, 0), 100),
      raw: `${m.max_drawdown.toFixed(1)}%`,
      better: "high",
    },
    {
      metric: "低波动性",
      value: Math.min(Math.max((1 - m.volatility / 35) * 100, 0), 100),
      raw: `${m.volatility.toFixed(1)}%`,
      better: "high",
    },
    {
      metric: "Beta稳定",
      value: Math.min(Math.max((1 - Math.abs(m.beta - 1)) * 100, 0), 100),
      raw: m.beta.toFixed(2),
      better: "high",
    },
    {
      metric: "超额Alpha",
      value: Math.min(Math.max(((m.alpha + 5) / 15) * 100, 0), 100),
      raw: `${m.alpha.toFixed(1)}%`,
      better: "high",
    },
    {
      metric: "年化收益",
      value: Math.min(Math.max(((yReturn + 20) / 60) * 100, 0), 100),
      raw: `${yReturn.toFixed(1)}%`,
      better: "high",
    },
  ];
}

// ════════════════════════════════════════
// 单个指标色块 (value 0-100)
// ════════════════════════════════════════

const MetricTile: React.FC<{ label: string; raw: string; value: number; color: string }> = ({
  label,
  raw,
  value,
  color,
}) => (
  <div
    style={{
      background: `${color}0D`,
      borderRadius: 8,
      padding: "10px 12px",
      border: `1px solid ${color}22`,
    }}
  >
    <Text type="secondary" style={{ fontSize: 11, display: "block" }}>
      {label}
    </Text>
    <Text strong style={{ fontSize: 20, color }}>
      {raw}
    </Text>
    {/* 进度条 */}
    <div style={{ marginTop: 4, height: 4, background: "#f0f0f0", borderRadius: 2, overflow: "hidden" }}>
      <div style={{ width: `${Math.round(value)}%`, height: "100%", background: color, borderRadius: 2 }} />
    </div>
  </div>
);

// ════════════════════════════════════════
// 主组件
// ════════════════════════════════════════

const FundRiskCard: React.FC<Props> = ({ fundCode }) => {
  const [data, setData] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/funds/${fundCode}/risk-metrics`);
      const json = await res.json();
      if (json.code === 0) setData(json.data as RiskData);
    } catch (err) {
      console.error("[风险卡片] 请求失败", err);
    } finally {
      setLoading(false);
    }
  }, [fundCode]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (!data && !loading) return null;

  const m = data?.metrics;
  const radarData = m ? normalizeRadar(m, data.returns.yearly) : [];
  const riskColor = RISK_COLORS[data?.risk_level ?? ""] ?? "#faad14";

  return (
    <Card
      size="small"
      style={{ borderRadius: 8, marginBottom: 12 }}
      styles={{ body: { padding: "12px 16px" } }}
      title={
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Text strong style={{ fontSize: 14 }}>
            ⚠️ {data?.fund_name ?? fundCode} 风险评估
          </Text>
          {data?.risk_level && (
            <Tag color={riskColor} style={{ margin: 0 }}>
              {data.risk_level}
            </Tag>
          )}
        </div>
      }
    >
      <Spin spinning={loading}>
        {data && m ? (
          <Row gutter={[12, 12]}>
            {/* ── 左侧：指标网格 3×2 ── */}
            <Col xs={24} md={13}>
              <Row gutter={[8, 8]}>
                <Col span={8}>
                  <MetricTile
                    label="Sharpe 比率"
                    raw={m.sharpe_ratio.toFixed(2)}
                    value={radarData[0].value}
                    color="#1677ff"
                  />
                </Col>
                <Col span={8}>
                  <MetricTile
                    label="最大回撤"
                    raw={`${m.max_drawdown.toFixed(1)}%`}
                    value={radarData[1].value}
                    color="#ff4d4f"
                  />
                </Col>
                <Col span={8}>
                  <MetricTile
                    label="年化波动"
                    raw={`${m.volatility.toFixed(1)}%`}
                    value={radarData[2].value}
                    color="#faad14"
                  />
                </Col>
                <Col span={8}>
                  <MetricTile
                    label="Beta  系数"
                    raw={m.beta.toFixed(2)}
                    value={radarData[3].value}
                    color="#722ed1"
                  />
                </Col>
                <Col span={8}>
                  <MetricTile
                    label="Alpha 超额"
                    raw={`${m.alpha.toFixed(1)}%`}
                    value={radarData[4].value}
                    color="#13c2c2"
                  />
                </Col>
                <Col span={8}>
                  <MetricTile
                    label="年化收益"
                    raw={`${data.returns.yearly.toFixed(1)}%`}
                    value={radarData[5].value}
                    color="#52c41a"
                  />
                </Col>
              </Row>
            </Col>

            {/* ── 右侧：雷达图 ── */}
            <Col xs={24} md={11}>
              <ResponsiveContainer width="100%" height={240}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#f0f0f0" />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: "#666" }} />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 100]}
                    tick={false}
                    axisLine={false}
                  />
                  <ReTooltip
                    contentStyle={{ borderRadius: 6, border: "1px solid #e8ecf1", fontSize: 12 }}
                    formatter={(value: number, _: string, item: any) => [`${item.payload.raw}`, item.payload.metric]}
                  />
                  <Radar
                    name={data.fund_name}
                    dataKey="value"
                    stroke={riskColor}
                    fill={riskColor}
                    fillOpacity={0.2}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </Col>
          </Row>
        ) : (
          !loading && (
            <div style={{ height: 260, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Empty description="暂无风险数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            </div>
          )
        )}
      </Spin>
    </Card>
  );
};

export default FundRiskCard;

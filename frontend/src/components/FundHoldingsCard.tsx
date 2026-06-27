import React, { useEffect, useState, useCallback } from "react";
import { Card, Spin, Empty, Typography, Row, Col } from "antd";
import { PieChartOutlined, BarChartOutlined } from "@ant-design/icons";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  PieChart as RePieChart,
  Pie,
  Legend,
} from "recharts";

const { Text } = Typography;

// ════════════════════════════════════════
// 类型
// ════════════════════════════════════════

interface HoldingItem {
  rank: number;
  stock_code: string;
  stock_name: string;
  shares: number;
  market_value: number;
  proportion: number;
}

interface HoldingsData {
  fund_code: string;
  fund_name: string;
  report_date: string;
  top_holdings: HoldingItem[];
  industry_distribution: Record<string, number>;
  asset_allocation: Record<string, number>;
}

interface FundHoldingsCardProps {
  fundCode: string;
}

// ════════════════════════════════════════
// 颜色
// ════════════════════════════════════════

const BAR_COLORS = [
  "#1677ff", "#4096ff", "#69b1ff", "#91caff", "#bae0ff",
  "#d6e4ff", "#e6f4ff",
];

const PIE_COLORS = [
  "#1677ff", "#52c41a", "#faad14", "#ff7a45", "#ff4d4f",
  "#722ed1", "#13c2c2", "#eb2f96", "#a0d911",
];

const ASSET_COLORS: Record<string, string> = {
  "股票": "#cf1322",
  "债券": "#1677ff",
  "现金": "#52c41a",
};

// ════════════════════════════════════════
// 千亿/亿格式化
// ════════════════════════════════════════

function fmtAmount(v: number): string {
  if (v >= 10000) return `${(v / 10000).toFixed(0)}亿`;
  return `${v.toFixed(0)}万`;
}

// ════════════════════════════════════════
// 组件
// ════════════════════════════════════════

const FundHoldingsCard: React.FC<FundHoldingsCardProps> = ({ fundCode }) => {
  const [data, setData] = useState<HoldingsData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/funds/${fundCode}/holdings`);
      const json = await res.json();
      if (json.code === 0) setData(json.data as HoldingsData);
    } catch (err) {
      console.error("[持仓卡片] 请求失败", err);
    } finally {
      setLoading(false);
    }
  }, [fundCode]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ── 数据处理 ──
  const topHoldings = data?.top_holdings ?? [];

  const industryList = data
    ? Object.entries(data.industry_distribution).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  const assetList = data
    ? Object.entries(data.asset_allocation).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  // ── 空数据 ──
  if (!data && !loading) return null;

  return (
    <Card
      size="small"
      style={{ borderRadius: 8, marginBottom: 12 }}
      styles={{ body: { padding: "12px 16px" } }}
      title={
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Text strong style={{ fontSize: 14 }}>
            🏢 {data?.fund_name ?? fundCode} 持仓分析
          </Text>
          {data?.report_date && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              报告期 {data.report_date}
            </Text>
          )}
        </div>
      }
    >
      <Spin spinning={loading}>
        {data ? (
          <Row gutter={[16, 16]}>
            {/* ── 区域一：前十大重仓股（横向条形图）── */}
            <Col xs={24} lg={14}>
              <div style={{ marginBottom: 4 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  <BarChartOutlined /> 重仓股持仓
                </Text>
              </div>
              <ResponsiveContainer width="100%" height={Math.max(topHoldings.length * 36, 180)}>
                <BarChart
                  data={topHoldings}
                  layout="vertical"
                  margin={{ top: 0, right: 20, bottom: 0, left: 70 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11, fill: "#999" }} tickFormatter={(v) => `${v}%`} />
                  <YAxis
                    type="category"
                    dataKey="stock_name"
                    tick={{ fontSize: 12, fill: "#333" }}
                    width={65}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 6,
                      border: "1px solid #e8ecf1",
                      fontSize: 12,
                      padding: "8px 12px",
                    }}
                    formatter={(value: number, name: string, item: any) => {
                      const p = item?.payload as HoldingItem;
                      return [`${value}%（市值约${fmtAmount(p.market_value)}）`, "持仓占比"];
                    }}
                  />
                  <Bar dataKey="proportion" radius={[0, 4, 4, 0]} maxBarSize={24}>
                    {topHoldings.map((_, i) => (
                      <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Col>

            {/* ── 区域二：行业分布（饼图）── */}
            <Col xs={24} lg={5}>
              <div style={{ marginBottom: 4 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  行业分布
                </Text>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <RePieChart>
                  <Pie
                    data={industryList}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {industryList.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ borderRadius: 6, border: "1px solid #e8ecf1", fontSize: 12 }}
                    formatter={(value: number) => [`${value}%`, "占比"]}
                  />
                  <Legend
                    layout="horizontal"
                    align="center"
                    verticalAlign="bottom"
                    wrapperStyle={{ fontSize: 11 }}
                  />
                </RePieChart>
              </ResponsiveContainer>
            </Col>

            {/* ── 区域三：资产配置（环形图）── */}
            <Col xs={24} lg={5}>
              <div style={{ marginBottom: 4 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  资产配置
                </Text>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <RePieChart>
                  <Pie
                    data={assetList}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {assetList.map((item) => (
                      <Cell
                        key={item.name}
                        fill={ASSET_COLORS[item.name] || PIE_COLORS[assetList.indexOf(item) % PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ borderRadius: 6, border: "1px solid #e8ecf1", fontSize: 12 }}
                    formatter={(value: number) => [`${value}%`, "占比"]}
                  />
                  <Legend
                    layout="horizontal"
                    align="center"
                    verticalAlign="bottom"
                    wrapperStyle={{ fontSize: 11 }}
                  />
                </RePieChart>
              </ResponsiveContainer>
            </Col>
          </Row>
        ) : (
          !loading && (
            <div style={{ height: 260, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Empty description="暂无持仓数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            </div>
          )
        )}
      </Spin>
    </Card>
  );
};

export default FundHoldingsCard;

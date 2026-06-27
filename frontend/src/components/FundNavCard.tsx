import React, { useEffect, useState, useCallback } from "react";
import { Card, Segmented, Typography, Spin, Tag, Empty } from "antd";
import { ArrowUpOutlined, ArrowDownOutlined } from "@ant-design/icons";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Area,
  ComposedChart,
} from "recharts";

const { Text, Title } = Typography;

// ════════════════════════════════════════
// 类型定义
// ════════════════════════════════════════

interface NavPoint {
  date: string;
  nav: number;
  change_pct: number;
}

interface FundNavCardProps {
  fundCode: string;
  fundName?: string;
  currentNav?: number;
  dailyChange?: number;
}

const RANGE_OPTIONS: { label: string; value: string }[] = [
  { label: "1周", value: "1w" },
  { label: "1月", value: "1m" },
  { label: "3月", value: "3m" },
  { label: "6月", value: "6m" },
  { label: "1年", value: "1y" },
];

// ════════════════════════════════════════
// 组件
// ════════════════════════════════════════

const FundNavCard: React.FC<FundNavCardProps> = ({
  fundCode,
  fundName,
  currentNav,
  dailyChange = 0,
}) => {
  const [range, setRange] = useState("1m");
  const [data, setData] = useState<NavPoint[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(
    async (r: string) => {
      setLoading(true);
      try {
        const res = await fetch(`/api/funds/${fundCode}/nav-history?range=${r}`);
        const json = await res.json();
        if (json.code === 0) setData(json.data as NavPoint[]);
      } catch (err) {
        console.error("[净值卡片] 请求失败", err);
      } finally {
        setLoading(false);
      }
    },
    [fundCode]
  );

  useEffect(() => {
    fetchData(range);
  }, [range, fetchData]);

  // ═══════════════ 颜色 ═══════════════
  const isUp = dailyChange >= 0;
  const upColor = "#cf1322"; // A 股红涨
  const downColor = "#389e0d"; // A 股绿跌
  const chartColor = isUp ? upColor : downColor;
  const gradientId = `navGradient-${fundCode}`;

  // ═══════════════ 计算 Y 轴范围（给上下留 5% 呼吸空间）═══════════════
  const navValues = data.map((d) => d.nav);
  const minNav = Math.min(...navValues, currentNav ?? Infinity);
  const maxNav = Math.max(...navValues, currentNav ?? -Infinity);
  const padding = (maxNav - minNav) * 0.1 || 0.01;
  const yDomain: [number, number] = [minNav - padding, maxNav + padding];

  return (
    <Card
      size="small"
      style={{ borderRadius: 8, marginBottom: 12 }}
      styles={{ body: { padding: "12px 16px" } }}
      title={
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 8,
          }}
        >
          {/* 名称 */}
          <Text strong style={{ fontSize: 14 }}>
            📈 {fundName || fundCode} 净值走势
          </Text>

          {/* 净值 + 涨跌 */}
          {currentNav != null && (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Title level={5} style={{ margin: 0, whiteSpace: "nowrap" }}>
                ¥{currentNav.toFixed(4)}
              </Title>
              <Tag
                color={isUp ? "red" : "green"}
                style={{ margin: 0, fontSize: 13, fontWeight: 500 }}
              >
                {isUp ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                {isUp ? "+" : ""}
                {dailyChange.toFixed(2)}%
              </Tag>
            </div>
          )}
        </div>
      }
    >
      {/* 时间范围选择 */}
      <div style={{ marginBottom: 12 }}>
        <Segmented
          size="small"
          options={RANGE_OPTIONS}
          value={range}
          onChange={(v) => setRange(v as string)}
        />
      </div>

      {/* 图表 */}
      <Spin spinning={loading}>
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height={260}>
            <ComposedChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={chartColor} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={chartColor} stopOpacity={0.02} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />

              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#999" }}
                tickLine={false}
                axisLine={{ stroke: "#e8ecf1" }}
                interval="preserveStartEnd"
                minTickGap={40}
              />

              <YAxis
                domain={yDomain}
                tick={{ fontSize: 11, fill: "#999" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => v.toFixed(3)}
                width={65}
              />

              <Tooltip
                contentStyle={{
                  borderRadius: 6,
                  border: "1px solid #e8ecf1",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                  fontSize: 12,
                  padding: "8px 12px",
                }}
                formatter={(value: number, name: string) => {
                  if (name === "nav") return [`¥${value.toFixed(4)}`, "单位净值"];
                  return [value, name];
                }}
                labelFormatter={(label: string) => `📅 ${label}`}
              />

              <Area
                type="monotone"
                dataKey="nav"
                stroke={chartColor}
                strokeWidth={2}
                fill={`url(#${gradientId})`}
                name="nav"
                dot={false}
                activeDot={{ r: 4, fill: chartColor, stroke: "#fff", strokeWidth: 2 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ height: 260, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Empty description="暂无净值数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          </div>
        )}
      </Spin>
    </Card>
  );
};

export default FundNavCard;

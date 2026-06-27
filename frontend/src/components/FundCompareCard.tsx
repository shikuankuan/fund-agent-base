import React, { useEffect, useState, useCallback, useMemo } from "react";
import { Card, Spin, Empty, Typography, Table, Tag } from "antd";
import { RiseOutlined, FallOutlined } from "@ant-design/icons";

const { Text } = Typography;

// ════════════════════════════════════════
// 类型
// ════════════════════════════════════════

interface CompareFund {
  fund_code: string;
  fund_name: string;
  fund_type: string;
  risk_level: string;
  company: string;
  scale: string;
  founded_date: string;
  manager: string;
  nav_current: number;
  nav_daily_change: number;
  nav_yearly_change: number;
  risk_metrics: {
    sharpe_ratio: number;
    max_drawdown: number;
    volatility: number;
    beta: number;
    alpha: number;
  };
}

interface Props {
  codes: string; // "000001,005827"
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
// 好坏阈值
// ════════════════════════════════════════

function isGood(metric: string, value: number): boolean {
  switch (metric) {
    case "max_drawdown": return Math.abs(value) < 20;
    case "sharpe_ratio": return value > 1;
    case "volatility": return value < 20;
    case "beta": return value > 0.7 && value < 1.3;
    case "alpha": return value > 2;
  }
  return true;
}

// ════════════════════════════════════════
// 指标定义
// ════════════════════════════════════════

interface MetricRow {
  key: string;
  label: string;
  isPercent?: boolean;
  decimals?: number;
}

const METRICS: MetricRow[] = [
  { key: "fund_type", label: "基金类型" },
  { key: "risk_level", label: "风险等级" },
  { key: "company", label: "基金公司" },
  { key: "manager", label: "基金经理" },
  { key: "founded_date", label: "成立日期" },
  { key: "scale", label: "基金规模" },
  { key: "nav_current", label: "最新净值", decimals: 4 },
  { key: "nav_daily_change", label: "日涨跌", isPercent: true },
  { key: "nav_yearly_change", label: "年化收益", isPercent: true, decimals: 2 },
  { key: "sharpe_ratio", label: "Sharpe 比率", decimals: 2 },
  { key: "max_drawdown", label: "最大回撤", isPercent: true, decimals: 1 },
  { key: "volatility", label: "年化波动", isPercent: true, decimals: 1 },
  { key: "beta", label: "Beta 系数", decimals: 2 },
  { key: "alpha", label: "Alpha 超额", isPercent: true, decimals: 1 },
];

// ════════════════════════════════════════
// 颜色条
// ════════════════════════════════════════

const CHART_COLORS = ["#1677ff", "#52c41a", "#faad14", "#ff7a45", "#ff4d4f", "#722ed1", "#13c2c2"];

// ════════════════════════════════════════
// 渲染单元格
// ════════════════════════════════════════

function renderCell(fund: CompareFund, metric: MetricRow) {
  let val: any;

  switch (metric.key) {
    case "risk_level":
      return <Tag color={RISK_COLOR[fund.risk_level]}>{fund.risk_level}</Tag>;
    case "fund_type":
      return <Text>{fund.fund_type}</Text>;
    case "company":
      return <Text>{fund.company}</Text>;
    case "manager":
      return <Text>{fund.manager}</Text>;
    case "founded_date":
      return <Text>{fund.founded_date}</Text>;
    case "scale":
      return <Text>{fund.scale}</Text>;
    case "nav_current":
      val = fund.nav_current;
      break;
    case "nav_daily_change":
      val = fund.nav_daily_change;
      break;
    case "nav_yearly_change":
      val = fund.nav_yearly_change;
      break;
    case "sharpe_ratio":
      val = fund.risk_metrics.sharpe_ratio;
      break;
    case "max_drawdown":
      val = fund.risk_metrics.max_drawdown;
      break;
    case "volatility":
      val = fund.risk_metrics.volatility;
      break;
    case "beta":
      val = fund.risk_metrics.beta;
      break;
    case "alpha":
      val = fund.risk_metrics.alpha;
      break;
    default:
      return <span>{val}</span>;
  }

  if (val === undefined || val === null) return <Text type="secondary">—</Text>;

  const decimals = metric.decimals ?? 2;
  const good = isGood(metric.key, val);

  // daily/yearly change coloring
  if (metric.key === "nav_daily_change" || metric.key === "nav_yearly_change") {
    const up = val >= 0;
    return (
      <span style={{ color: up ? "#cf1322" : "#3f8600", fontWeight: 600 }}>
        {up ? <RiseOutlined /> : <FallOutlined />} {val > 0 ? "+" : ""}
        {val.toFixed(decimals)}%
      </span>
    );
  }

  // risk metrics coloring
  const suffix = metric.isPercent ? "%" : "";
  const color = good ? "#52c41a" : "#ff4d4f";
  return (
    <span style={{ color, fontWeight: 600 }}>
      {typeof val === "number" ? val.toFixed(decimals) : val}{suffix}
    </span>
  );
}

// ════════════════════════════════════════
// 主组件
// ════════════════════════════════════════

const FundCompareCard: React.FC<Props> = ({ codes }) => {
  const [data, setData] = useState<CompareFund[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    console.log("[FundCompareCard] codes=", codes);
    setLoading(true);
    try {
      const res = await fetch(`/api/funds/compare?codes=${encodeURIComponent(codes)}`);
      const json = await res.json();
      console.log("[FundCompareCard] response=", json);
      if (json.code === 0) setData(json.data as CompareFund[]);
    } catch (err) {
      console.error("[对比卡片] 请求失败", err);
    } finally {
      setLoading(false);
    }
  }, [codes]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (data.length === 0 && !loading) return null;

  // ── 构建对比表格 dataSource ──
  const tableData = METRICS.map((m) => {
    const row: any = { key: m.key, label: m.label };
    data.forEach((f) => {
      row[f.fund_code] = renderCell(f, m);
    });
    return row;
  });

  // ── 构建图表数据 ──
  const chartData = data.map((f, i) => ({
    name: f.fund_name,
    code: f.fund_code,
    年化收益: f.nav_yearly_change,
    Sharpe: f.risk_metrics.sharpe_ratio,
    抗回撤: 100 - Math.abs(f.risk_metrics.max_drawdown),
    Alpha: f.risk_metrics.alpha,
    fill: CHART_COLORS[i % CHART_COLORS.length],
  }));

  const chartColumns: any[] = [
    {
      title: "指标",
      dataIndex: "label",
      key: "label",
      fixed: "left" as const,
      width: 110,
      render: (t: string) => <Text strong>{t}</Text>,
    },
    ...data.map((f, i) => ({
      title: (
        <div style={{ textAlign: "center" }}>
          <Text strong style={{ fontSize: 13, color: CHART_COLORS[i % CHART_COLORS.length] }}>
            {f.fund_name}
          </Text>
          <br />
          <Text type="secondary" style={{ fontSize: 11 }}>
            {f.fund_code}
          </Text>
        </div>
      ),
      dataIndex: f.fund_code,
      key: f.fund_code,
      align: "center" as const,
      render: (node: React.ReactNode) => node,
    })),
  ];

  return (
    <Card
      size="small"
      style={{ borderRadius: 8, marginBottom: 12 }}
      styles={{ body: { padding: "12px 16px" } }}
      title={
        <Text strong style={{ fontSize: 14 }}>
          📊 基金对比
        </Text>
      }
    >
      <Spin spinning={loading}>
        {data.length > 0 ? (
          <>
            {/* ── 对比表格 ── */}
            <Table
              columns={chartColumns}
              dataSource={tableData}
              pagination={false}
              size="small"
              bordered
              scroll={{ x: "max-content" }}
            />

            {/* ── 彩条图例（纯色块） ── */}
            <div style={{ marginTop: 12, marginBottom: 4 }}>
              <Text type="secondary" style={{ fontSize: 11 }}>
                ▼ 关键指标横向对比
              </Text>
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              {(["年化收益", "Sharpe", "抗回撤", "Alpha"] as const).map((metric) => {
                const maxVal = Math.max(...chartData.map((d) => d[metric]), 0.1);
                return (
                  <div key={metric} style={{ flex: 1, minWidth: 140 }}>
                    <Text type="secondary" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>
                      {metric}
                    </Text>
                    {chartData.map((d, i) => (
                      <div key={d.code} style={{ display: "flex", alignItems: "center", marginBottom: 3, gap: 6 }}>
                        <div
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: 2,
                            background: CHART_COLORS[i % CHART_COLORS.length],
                            flexShrink: 0,
                          }}
                        />
                        <Text style={{ fontSize: 12, width: 80, flexShrink: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={d.name}>
                          {d.name}
                        </Text>
                        <div style={{ flex: 1, height: 14, background: "#f0f0f0", borderRadius: 3, overflow: "hidden" }}>
                          <div
                            style={{
                              width: `${Math.min((d[metric] / maxVal) * 100, 100)}%`,
                              height: "100%",
                              background: CHART_COLORS[i % CHART_COLORS.length],
                              borderRadius: 3,
                              transition: "width 0.5s",
                            }}
                          />
                        </div>
                        <Text strong style={{ fontSize: 12, width: 50, textAlign: "right" }}>
                          {metric === "抗回撤" ? `${d[metric].toFixed(0)}%` : d[metric].toFixed(2)}
                        </Text>
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          !loading && (
            <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Empty description="暂无对比数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            </div>
          )
        )}
      </Spin>
    </Card>
  );
};

export default FundCompareCard;

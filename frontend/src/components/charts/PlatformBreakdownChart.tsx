import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const PLATFORM_COLORS: Record<string, string> = {
  reddit: "#f97316",
  hackernews: "#ea580c",
  twitter: "#0ea5e9",
  stackoverflow: "#eab308",
  github: "#6366f1",
  default: "#94a3b8",
};

interface PlatformBreakdownChartProps {
  labels: string[];
  counts: number[];
}

export function PlatformBreakdownChart({ labels, counts }: PlatformBreakdownChartProps) {
  const chartData = labels.map((label, i) => ({
    platform: label,
    count: counts[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
        <XAxis type="number" stroke="#94a3b8" tick={{ fontSize: 12 }} />
        <YAxis
          type="category"
          dataKey="platform"
          stroke="#94a3b8"
          tick={{ fontSize: 12 }}
          width={100}
        />
        <Tooltip
          contentStyle={{
            borderRadius: "0.75rem",
            border: "1px solid #e2e8f0",
            boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
          }}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
          {chartData.map((entry) => (
            <Cell
              key={entry.platform}
              fill={PLATFORM_COLORS[entry.platform.toLowerCase()] ?? PLATFORM_COLORS.default}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

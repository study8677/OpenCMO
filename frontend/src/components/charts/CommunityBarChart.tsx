import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { CommunityChartData } from "../../types";

export function CommunityBarChart({ data }: { data: CommunityChartData }) {
  const chartData = data.scan_labels.map((label, i) => ({
    date: label,
    hits: data.scan_hits[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="communityGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            borderRadius: "0.75rem",
            border: "1px solid #e2e8f0",
            boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
          }}
        />
        <Area
          type="monotone"
          dataKey="hits"
          stroke="#f59e0b"
          strokeWidth={2.5}
          fill="url(#communityGradient)"
          activeDot={{ r: 5, strokeWidth: 2, fill: "#fff" }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

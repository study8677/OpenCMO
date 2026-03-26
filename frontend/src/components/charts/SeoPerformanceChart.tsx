import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
} from "recharts";
import type { ChartData } from "../../types";

export function SeoPerformanceChart({ data }: { data: ChartData }) {
  const chartData = data.labels.map((label, i) => ({
    date: label,
    performance: (data.performance as (number | null)[])[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="seoGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <ReferenceArea y1={0.9} y2={1} fill="#dcfce7" fillOpacity={0.3} />
        <ReferenceArea y1={0} y2={0.5} fill="#fef2f2" fillOpacity={0.3} />
        <ReferenceLine
          y={0.9}
          stroke="#16a34a"
          strokeDasharray="3 3"
          label={{ value: "Good", position: "right", fontSize: 11, fill: "#16a34a" }}
        />
        <ReferenceLine
          y={0.5}
          stroke="#dc2626"
          strokeDasharray="3 3"
          label={{ value: "Needs Work", position: "right", fontSize: 11, fill: "#dc2626" }}
        />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94a3b8" />
        <YAxis
          domain={[0, 1]}
          tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
          stroke="#94a3b8"
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          formatter={(v: number) => [`${Math.round(v * 100)}%`, "Performance"]}
          contentStyle={{
            borderRadius: "0.75rem",
            border: "1px solid #e2e8f0",
            boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
          }}
        />
        <Area
          type="monotone"
          dataKey="performance"
          stroke="#0ea5e9"
          strokeWidth={2.5}
          fill="url(#seoGradient)"
          activeDot={{ r: 5, strokeWidth: 2, fill: "#fff" }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

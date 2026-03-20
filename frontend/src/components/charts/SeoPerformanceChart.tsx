import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { ChartData } from "../../types";

export function SeoPerformanceChart({ data }: { data: ChartData }) {
  const chartData = data.labels.map((label, i) => ({
    date: label,
    performance: (data.performance as (number | null)[])[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 1]} tickFormatter={(v: number) => `${Math.round(v * 100)}%`} />
        <Tooltip formatter={(v: number) => `${Math.round(v * 100)}%`} />
        <Line type="monotone" dataKey="performance" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

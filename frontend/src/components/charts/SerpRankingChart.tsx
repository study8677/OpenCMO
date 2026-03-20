import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { SerpChartData } from "../../types";

const COLORS = ["#2563eb", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#06b6d4", "#ec4899"];

export function SerpRankingChart({ data }: { data: SerpChartData }) {
  const chartData = data.labels.map((label, i) => {
    const point: Record<string, string | number | null> = { date: label };
    for (const kw of data.keywords) {
      point[kw] = data.positions[kw]?.[i] ?? null;
    }
    return point;
  });

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis reversed domain={[1, "auto"]} label={{ value: "Position", angle: -90, position: "insideLeft" }} />
        <Tooltip />
        <Legend />
        {data.keywords.map((kw, i) => (
          <Line
            key={kw}
            type="monotone"
            dataKey={kw}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={{ r: 3 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

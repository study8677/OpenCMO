import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
} from "recharts";
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

  // Show top 5 keywords by best position
  const displayKeywords = data.keywords.slice(0, 5);

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <ReferenceArea y1={1} y2={3} fill="#dcfce7" fillOpacity={0.3} />
        <ReferenceArea y1={4} y2={10} fill="#dbeafe" fillOpacity={0.2} />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94a3b8" />
        <YAxis
          reversed
          domain={[1, "auto"]}
          stroke="#94a3b8"
          tick={{ fontSize: 12 }}
          label={{ value: "Position", angle: -90, position: "insideLeft", style: { fontSize: 12, fill: "#94a3b8" } }}
        />
        <Tooltip
          contentStyle={{
            borderRadius: "0.75rem",
            border: "1px solid #e2e8f0",
            boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
          }}
        />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
        {displayKeywords.map((kw, i) => (
          <Line
            key={kw}
            type="monotone"
            dataKey={kw}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2.5}
            dot={{ r: 3 }}
            activeDot={{ r: 5, strokeWidth: 2, fill: "#fff" }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { ChartData } from "../../types";

const SERIES = [
  { key: "GEO Score", color: "#10b981", opacity: 0.15 },
  { key: "Visibility", color: "#8b5cf6", opacity: 0.1 },
  { key: "Position", color: "#0ea5e9", opacity: 0.1 },
  { key: "Sentiment", color: "#f59e0b", opacity: 0.1 },
];

export function GeoScoreChart({ data }: { data: ChartData }) {
  const chartData = data.labels.map((label, i) => ({
    date: label,
    "GEO Score": (data.geo_score as (number | null)[])[i],
    Visibility: (data.visibility as (number | null)[])[i],
    Position: (data.position as (number | null)[])[i],
    Sentiment: (data.sentiment as (number | null)[])[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <AreaChart data={chartData}>
        <defs>
          {SERIES.map((s) => (
            <linearGradient key={s.key} id={`geo-${s.key.replace(/\s/g, "")}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={s.color} stopOpacity={s.opacity} />
              <stop offset="95%" stopColor={s.color} stopOpacity={0.01} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94a3b8" />
        <YAxis domain={[0, 100]} stroke="#94a3b8" tick={{ fontSize: 12 }} />
        <ReferenceLine
          y={70}
          stroke="#10b981"
          strokeDasharray="3 3"
          label={{ value: "Target", position: "right", fontSize: 11, fill: "#10b981" }}
        />
        <Tooltip
          contentStyle={{
            borderRadius: "0.75rem",
            border: "1px solid #e2e8f0",
            boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
          }}
        />
        <Legend
          iconType="circle"
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
        />
        {SERIES.map((s) => (
          <Area
            key={s.key}
            type="monotone"
            dataKey={s.key}
            stroke={s.color}
            strokeWidth={2}
            fill={`url(#geo-${s.key.replace(/\s/g, "")})`}
            activeDot={{ r: 4, strokeWidth: 2, fill: "#fff" }}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

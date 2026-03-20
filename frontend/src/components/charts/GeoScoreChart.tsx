import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { ChartData } from "../../types";

export function GeoScoreChart({ data }: { data: ChartData }) {
  const chartData = data.labels.map((label, i) => ({
    date: label,
    "GEO Score": (data.geo_score as (number | null)[])[i],
    Visibility: (data.visibility as (number | null)[])[i],
    Position: (data.position as (number | null)[])[i],
    Sentiment: (data.sentiment as (number | null)[])[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="GEO Score" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
        <Line type="monotone" dataKey="Visibility" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
        <Line type="monotone" dataKey="Position" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} />
        <Line type="monotone" dataKey="Sentiment" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

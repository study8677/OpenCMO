import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface CwvMiniChartProps {
  data: { date: string; value: number | null }[];
  label: string;
  color: string;
  thresholds: [number, number];
  unit: string;
}

export function CwvMiniChart({ data, label, color, thresholds, unit }: CwvMiniChartProps) {
  const gradientId = `cwv-${label.replace(/\s/g, "")}`;

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.2} />
            <stop offset="95%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#94a3b8" />
        <YAxis tick={{ fontSize: 10 }} stroke="#94a3b8" />
        <Tooltip
          formatter={(v: number) => [`${v}${unit}`, label]}
          contentStyle={{
            borderRadius: "0.75rem",
            border: "1px solid #e2e8f0",
            boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
            fontSize: 12,
          }}
        />
        <ReferenceLine
          y={thresholds[0]}
          stroke="#16a34a"
          strokeDasharray="3 3"
          label={{ value: "Good", position: "right", fontSize: 10, fill: "#16a34a" }}
        />
        <ReferenceLine
          y={thresholds[1]}
          stroke="#dc2626"
          strokeDasharray="3 3"
          label={{ value: "Poor", position: "right", fontSize: 10, fill: "#dc2626" }}
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          fill={`url(#${gradientId})`}
          activeDot={{ r: 4, strokeWidth: 2, fill: "#fff" }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

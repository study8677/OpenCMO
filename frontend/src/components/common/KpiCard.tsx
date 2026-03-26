import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export interface KpiCardProps {
  icon: React.ElementType;
  label: string;
  value: string | number | null;
  delta?: number | null;
  status?: "good" | "warning" | "poor";
  accentBg?: string;
  accentText?: string;
}

const statusColors = {
  good: "bg-emerald-500",
  warning: "bg-amber-500",
  poor: "bg-rose-500",
};

export function KpiCard({
  icon: Icon,
  label,
  value,
  delta,
  status,
  accentBg = "bg-sky-50",
  accentText = "text-sky-600",
}: KpiCardProps) {
  const deltaColor =
    delta != null && delta > 0
      ? "text-emerald-600"
      : delta != null && delta < 0
        ? "text-rose-500"
        : "text-zinc-400";

  const DeltaIcon =
    delta != null && delta > 0
      ? TrendingUp
      : delta != null && delta < 0
        ? TrendingDown
        : Minus;

  return (
    <div className="relative flex items-center gap-3 overflow-hidden rounded-xl border border-zinc-100 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${accentBg} ${accentText}`}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-2xl font-bold text-zinc-800">
            {value ?? "—"}
          </span>
          {delta != null && (
            <span className={`flex items-center gap-0.5 text-xs font-medium ${deltaColor}`}>
              <DeltaIcon className="h-3 w-3" />
              {Math.abs(delta).toFixed(1)}%
            </span>
          )}
        </div>
        <div className="text-xs text-zinc-500">{label}</div>
      </div>
      {status && (
        <div
          className={`absolute bottom-0 left-0 h-1 w-full ${statusColors[status]}`}
        />
      )}
    </div>
  );
}

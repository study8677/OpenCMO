import type { SerpSnapshot } from "../../types";

const BUCKETS = [
  { label: "Top 3", min: 1, max: 3, bg: "bg-emerald-500", text: "text-white" },
  { label: "4–10", min: 4, max: 10, bg: "bg-sky-500", text: "text-white" },
  { label: "11–20", min: 11, max: 20, bg: "bg-amber-400", text: "text-amber-900" },
  { label: "20+", min: 21, max: Infinity, bg: "bg-rose-400", text: "text-white" },
];

export function SerpDistributionBar({ data }: { data: SerpSnapshot[] }) {
  const ranked = data.filter((s) => s.position != null);
  if (!ranked.length) return null;

  const counts = BUCKETS.map((b) => ({
    ...b,
    count: ranked.filter((s) => s.position! >= b.min && s.position! <= b.max).length,
  }));

  const total = ranked.length;

  return (
    <div>
      <div className="flex h-8 overflow-hidden rounded-lg">
        {counts.map((b) =>
          b.count > 0 ? (
            <div
              key={b.label}
              className={`${b.bg} ${b.text} flex items-center justify-center text-xs font-semibold transition-all`}
              style={{ width: `${(b.count / total) * 100}%` }}
              title={`${b.label}: ${b.count}`}
            >
              {b.count}
            </div>
          ) : null,
        )}
      </div>
      <div className="mt-2 flex gap-4 text-xs text-zinc-500">
        {counts.map((b) => (
          <div key={b.label} className="flex items-center gap-1.5">
            <div className={`h-2.5 w-2.5 rounded-sm ${b.bg}`} />
            {b.label} ({b.count})
          </div>
        ))}
      </div>
    </div>
  );
}

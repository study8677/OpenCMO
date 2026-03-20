const COLORS = {
  green: "bg-emerald-50 text-emerald-700 ring-emerald-100",
  blue: "bg-sky-50 text-sky-700 ring-sky-100",
  purple: "bg-violet-50 text-violet-700 ring-violet-100",
  gray: "bg-slate-50 text-slate-500 ring-slate-100",
  red: "bg-rose-50 text-rose-700 ring-rose-100",
};

export function StatusBadge({
  label,
  value,
  color = "gray",
}: {
  label: string;
  value: string;
  color?: keyof typeof COLORS;
}) {
  return (
    <div className={`rounded-xl p-2.5 text-center ring-1 ring-inset ${COLORS[color]}`}>
      <p className="text-[10px] font-semibold uppercase tracking-wide opacity-70">{label}</p>
      <p className="mt-0.5 text-sm font-bold">{value}</p>
    </div>
  );
}

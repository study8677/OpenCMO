interface ChartCardProps {
  title: string;
  subtitle?: string;
  accentBorder?: string;
  children: React.ReactNode;
}

export function ChartCard({
  title,
  subtitle,
  accentBorder = "border-l-sky-500",
  children,
}: ChartCardProps) {
  return (
    <div className="rounded-xl border border-zinc-100 bg-white p-6 shadow-sm">
      <div className={`mb-4 border-l-4 ${accentBorder} pl-3`}>
        <h3 className="text-sm font-semibold text-zinc-700">{title}</h3>
        {subtitle && (
          <p className="text-xs text-zinc-400">{subtitle}</p>
        )}
      </div>
      {children}
    </div>
  );
}

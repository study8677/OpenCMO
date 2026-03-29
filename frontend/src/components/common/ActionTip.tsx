import type { ElementType } from "react";
import { Link } from "react-router";
import { CheckCircle2, AlertTriangle, AlertCircle } from "lucide-react";

type Severity = "success" | "warning" | "danger";

const SEVERITY_STYLES: Record<Severity, { border: string; bg: string; icon: ElementType; iconColor: string }> = {
  success: { border: "border-l-emerald-500", bg: "bg-emerald-50/60", icon: CheckCircle2, iconColor: "text-emerald-600" },
  warning: { border: "border-l-amber-500", bg: "bg-amber-50/60", icon: AlertTriangle, iconColor: "text-amber-600" },
  danger: { border: "border-l-rose-500", bg: "bg-rose-50/60", icon: AlertCircle, iconColor: "text-rose-600" },
};

export function ActionTip({
  title,
  severity = "warning",
  actionLabel,
  actionTo,
}: {
  title: string;
  severity?: Severity;
  actionLabel?: string;
  actionTo?: string;
}) {
  const style = SEVERITY_STYLES[severity];
  const Icon = style.icon;

  return (
    <div className={`flex items-start gap-3 rounded-xl border-l-4 ${style.border} ${style.bg} p-4 transition-all`}>
      <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${style.iconColor}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm leading-relaxed text-slate-700">{title}</p>
      </div>
      {actionLabel && actionTo && (
        <Link
          to={actionTo}
          className="shrink-0 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 hover:shadow"
        >
          {actionLabel}
        </Link>
      )}
    </div>
  );
}

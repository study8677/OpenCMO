import { Link } from "react-router";
import { Trash2, Clock, ExternalLink } from "lucide-react";
import type { Monitor } from "../../types";
import { RunScanButton } from "./RunScanButton";
import { useI18n } from "../../i18n";

export function MonitorList({
  monitors,
  onDelete,
}: {
  monitors: Monitor[];
  onDelete: (id: number) => void;
}) {
  const { t } = useI18n();

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {monitors.map((m) => (
        <div
          key={m.id}
          className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-200 hover:shadow-md"
        >
          <div className="mb-3 flex items-start justify-between">
            <div className="min-w-0 flex-1">
              <Link
                to={`/projects/${m.project_id}`}
                className="text-base font-semibold text-slate-900 hover:text-indigo-600"
              >
                {m.brand_name}
              </Link>
              <a
                href={m.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-0.5 flex items-center gap-1 text-xs text-slate-400 hover:text-indigo-500"
              >
                <span className="truncate">{m.url}</span>
                <ExternalLink size={10} className="shrink-0" />
              </a>
            </div>
            <span className="ml-2 shrink-0 rounded-lg bg-indigo-50 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-indigo-600">
              {m.job_type}
            </span>
          </div>

          <div className="mb-4 flex items-center gap-3 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Clock size={12} />
              {m.cron_expr}
            </span>
            <span className="text-slate-300">|</span>
            <span>{t("monitorList.lastRun")}: {m.last_run_at?.slice(0, 10) ?? t("common.never")}</span>
          </div>

          <div className="flex items-center justify-between border-t border-slate-100 pt-3">
            <RunScanButton monitorId={m.id} projectId={m.project_id} />
            <button
              onClick={() => onDelete(m.id)}
              className="rounded-lg p-2 text-slate-300 transition-colors hover:bg-rose-50 hover:text-rose-500"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

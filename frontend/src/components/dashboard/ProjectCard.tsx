import { Link } from "react-router";
import { Activity, Trash2 } from "lucide-react";
import type { Project } from "../../types";
import { useI18n } from "../../i18n";

import { utcDate } from "../../utils/time";

function formatRelativeTime(dateStr: string): string {
  const diff = Date.now() - utcDate(dateStr).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

export function ProjectCard({ project, onDelete }: { project: Project; onDelete?: (id: number) => void }) {
  const { latest } = project;
  const { t } = useI18n();

  const seoScore = latest?.seo?.score ?? null;
  const dotColor =
    seoScore == null ? "bg-slate-300"
    : seoScore >= 0.7 ? "bg-emerald-500"
    : seoScore >= 0.4 ? "bg-amber-400"
    : "bg-rose-500";

  const scannedAt = latest?.seo?.scanned_at ?? null;

  return (
    <Link
      to={`/projects/${project.id}`}
      className="group block overflow-hidden rounded-2xl bg-white p-4 ring-1 ring-slate-200/60 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:ring-slate-300"
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-400 transition-colors group-hover:bg-slate-100 group-hover:text-slate-800">
              <Activity size={16} strokeWidth={2} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold text-slate-800 tracking-tight leading-tight truncate">{project.brand_name}</h3>
                <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${dotColor}`} />
              </div>
              <p className="mt-0.5 text-xs text-slate-400 truncate">{project.url}</p>
            </div>
          </div>
        </div>
        <div className="ml-3 flex items-center gap-2 shrink-0">
          <span className="rounded-md bg-slate-50 px-2 py-1 text-[10px] font-medium tracking-wider text-slate-500 uppercase">
            {project.category === "auto" ? t("project.categoryAuto") : project.category}
          </span>
          {onDelete && (
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onDelete(project.id);
              }}
              title="Delete project"
              className="rounded-lg p-1.5 text-slate-300 opacity-0 transition-all duration-200 group-hover:opacity-100 hover:!bg-rose-50 hover:!text-rose-500 hover:scale-105 active:scale-95"
            >
              <Trash2 size={14} strokeWidth={1.5} />
            </button>
          )}
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-400">
        {scannedAt ? formatRelativeTime(scannedAt) : t("projectCard.noScans")}
      </p>
    </Link>
  );
}

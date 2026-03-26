import { Link } from "react-router";
import { ExternalLink, Activity, Trash2 } from "lucide-react";
import type { Project } from "../../types";
import { StatusBadge } from "./StatusBadge";
import { useI18n } from "../../i18n";

function ScoreBar({ label, value, max, suffix = "", color, trackColor }: {
  label: string; value: number | null; max: number; suffix?: string;
  color: string; trackColor: string;
}) {
  const pct = value != null ? Math.min(100, Math.round((value / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-10 text-[11px] font-medium text-slate-500">{label}</span>
      <div className={`h-2 flex-1 rounded-full ${trackColor}`}>
        <div
          className={`h-2 rounded-full transition-all duration-700 ease-out ${color}`}
          style={{ width: value != null ? `${pct}%` : "0%" }}
        />
      </div>
      <span className="w-10 text-right text-xs font-semibold text-slate-700">
        {value != null ? `${value}${suffix}` : "—"}
      </span>
    </div>
  );
}

export function ProjectCard({ project, onDelete }: { project: Project; onDelete?: (id: number) => void }) {
  const { latest } = project;
  const { t } = useI18n();

  return (
    <Link
      to={`/projects/${project.id}`}
      className="group block overflow-hidden rounded-2xl bg-white p-6 ring-1 ring-slate-200/60 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:ring-slate-300"
    >
      <div className="mb-6 flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-400 transition-colors group-hover:bg-slate-100 group-hover:text-slate-800">
              <Activity size={18} strokeWidth={2} />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-slate-800 tracking-tight leading-tight">{project.brand_name}</h3>
              <p className="flex items-center gap-1.5 mt-0.5 text-xs text-slate-400 transition-colors group-hover:text-slate-600">
                <span className="truncate">{project.url}</span>
                <ExternalLink size={12} className="shrink-0 opacity-50 transition-opacity group-hover:opacity-100" />
              </p>
            </div>
          </div>
        </div>
        <div className="ml-4 flex items-center gap-2">
          <span className="shrink-0 rounded-md bg-slate-50 px-2 py-1 text-[10px] font-medium tracking-wider text-slate-500 uppercase">
            {project.category}
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
              <Trash2 size={16} strokeWidth={1.5} />
            </button>
          )}
        </div>
      </div>

      {/* Score bars */}
      <div className="space-y-3">
        <ScoreBar
          label={t("project.seo")}
          value={latest?.seo?.score != null ? Math.round(latest.seo.score * 100) : null}
          max={100}
          suffix="%"
          color="bg-sky-500"
          trackColor="bg-sky-100"
        />
        <ScoreBar
          label={t("project.geo")}
          value={latest?.geo?.score ?? null}
          max={100}
          color="bg-emerald-500"
          trackColor="bg-emerald-100"
        />
      </div>

      {/* Bottom metrics */}
      <div className="mt-4 flex items-center gap-4 border-t border-slate-100 pt-4">
        <StatusBadge
          label={t("project.community")}
          value={latest?.community?.total_hits != null ? t("projectCard.hits", { count: latest.community.total_hits }) : "—"}
          color={latest?.community?.total_hits ? "blue" : "gray"}
        />
        <StatusBadge
          label={t("project.serp")}
          value={latest?.serp?.length ? t("projectCard.kw", { count: latest.serp.length }) : "—"}
          color={latest?.serp?.length ? "purple" : "gray"}
        />
      </div>
    </Link>
  );
}

import { Link } from "react-router";
import { ExternalLink } from "lucide-react";
import type { Project } from "../../types";
import { StatusBadge } from "./StatusBadge";
import { useI18n } from "../../i18n";

export function ProjectCard({ project }: { project: Project }) {
  const { latest } = project;
  const { t } = useI18n();

  return (
    <Link
      to={`/projects/${project.id}`}
      className="block rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="mb-4 flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-slate-900">{project.brand_name}</h3>
          <p className="mt-0.5 flex items-center gap-1 text-xs text-slate-400">
            <span className="truncate">{project.url}</span>
            <ExternalLink size={10} className="shrink-0" />
          </p>
        </div>
        <span className="ml-2 shrink-0 rounded-lg bg-slate-100 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          {project.category}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <StatusBadge
          label={t("project.seo")}
          value={latest?.seo?.score != null ? `${Math.round(latest.seo.score * 100)}%` : "—"}
          color={latest?.seo?.score != null && latest.seo.score >= 0.8 ? "green" : "gray"}
        />
        <StatusBadge
          label={t("project.geo")}
          value={latest?.geo?.score != null ? `${latest.geo.score}/100` : "—"}
          color={latest?.geo?.score != null && latest.geo.score >= 60 ? "green" : "gray"}
        />
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

import { Link } from "react-router";
import { ExternalLink, MessageSquare, PauseCircle, PlayCircle } from "lucide-react";
import type { Project } from "../../types";
import { useI18n } from "../../i18n";
import { useSetProjectPause } from "../../hooks/useProject";

export function ProjectHeader({ project, isPaused }: { project: Project; isPaused?: boolean }) {
  const { t } = useI18n();
  const setPause = useSetProjectPause();

  const handleTogglePause = () => {
    setPause.mutate({ id: project.id, pause: !isPaused });
  };

  return (
    <div className="mb-10 flex flex-col md:flex-row md:items-start justify-between gap-4">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">{project.brand_name}</h1>
          <span className="rounded-lg bg-slate-100 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            {project.category === "auto" ? t("project.categoryAuto") : project.category}
          </span>
        </div>
        <a
          href={project.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors"
        >
          {project.url} <ExternalLink size={14} />
        </a>
      </div>

      <div className="flex items-center gap-2 self-start">
        {isPaused !== undefined && (
          <button
            onClick={handleTogglePause}
            disabled={setPause.isPending}
            className={`inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition-colors ${
              isPaused
                ? "border-emerald-200 bg-emerald-50 text-emerald-700 hover:border-emerald-300 hover:bg-emerald-100"
                : "border-amber-200 bg-amber-50 text-amber-700 hover:border-amber-300 hover:bg-amber-100"
            }`}
          >
            {isPaused ? <PlayCircle size={16} /> : <PauseCircle size={16} />}
            {isPaused ? t("projectHeader.resume") : t("projectHeader.pause")}
          </button>
        )}
        <Link
          to={`/chat?project_id=${project.id}`}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm font-medium text-indigo-700 transition-colors hover:border-indigo-300 hover:bg-indigo-100"
        >
          <MessageSquare size={16} />
          {t("chat.discussProject")}
        </Link>
      </div>
    </div>
  );
}

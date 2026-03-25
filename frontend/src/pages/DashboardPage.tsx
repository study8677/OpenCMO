import { Link } from "react-router";
import { useProjects, useDeleteProject } from "../hooks/useProjects";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { ProjectCard } from "../components/dashboard/ProjectCard";
import { GlobalOverview } from "../components/dashboard/GlobalOverview";
import { InsightBanner } from "../components/dashboard/InsightBanner";
import { useI18n } from "../i18n";
import { Plus } from "lucide-react";

export function DashboardPage() {
  const { data: projects, isLoading, error } = useProjects();
  const deleteProject = useDeleteProject();
  const { t } = useI18n();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error.message} />;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      <div className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">{t("dashboard.title")}</h1>
          <p className="text-[15px] text-slate-500 mt-1.5">Overview of your AI marketing campaigns</p>
        </div>
        <Link
          to="/monitors"
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:bg-slate-800 hover:shadow-md active:scale-95"
        >
          <Plus size={16} />
          {t("dashboard.newMonitor")}
        </Link>
      </div>
      <InsightBanner />
      <GlobalOverview />
      {!projects?.length ? (
        <EmptyState
          title={t("dashboard.noProjects")}
          description={t("dashboard.noProjectsDesc")}
          action={
            <Link
              to="/monitors"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-6 py-3 text-sm font-medium text-white transition-all duration-200 hover:bg-slate-800 hover:shadow-md active:scale-95 mt-4"
            >
              <Plus size={16} />
              {t("dashboard.createMonitor")}
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <ProjectCard
              key={p.id}
              project={p}
              onDelete={(id) => deleteProject.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

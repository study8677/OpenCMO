import { Link } from "react-router";
import { useProjects } from "../hooks/useProjects";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { ProjectCard } from "../components/dashboard/ProjectCard";
import { useI18n } from "../i18n";
import { Plus } from "lucide-react";

export function DashboardPage() {
  const { data: projects, isLoading, error } = useProjects();
  const { t } = useI18n();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error.message} />;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t("dashboard.title")}</h1>
        <Link
          to="/monitors"
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-indigo-700 hover:shadow-md"
        >
          <Plus size={16} />
          {t("dashboard.newMonitor")}
        </Link>
      </div>
      {!projects?.length ? (
        <EmptyState
          title={t("dashboard.noProjects")}
          description={t("dashboard.noProjectsDesc")}
          action={
            <Link
              to="/monitors"
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-indigo-700 hover:shadow-md"
            >
              <Plus size={16} />
              {t("dashboard.createMonitor")}
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}
    </div>
  );
}

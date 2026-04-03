import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useProjects, useDeleteProject } from "../hooks/useProjects";
import { useCreateMonitor } from "../hooks/useMonitors";
import { useTaskPoll } from "../hooks/useTasks";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { AnimatedPage } from "../components/common/AnimatedPage";
import { SkeletonCard } from "../components/common/SkeletonCard";
import { ProjectCard } from "../components/dashboard/ProjectCard";
import { GlobalOverview } from "../components/dashboard/GlobalOverview";
import { InsightBanner } from "../components/dashboard/InsightBanner";
import { SetupBanner } from "../components/dashboard/SetupBanner";
import { MonitorForm } from "../components/monitors/MonitorForm";
import { AnalysisDialog } from "../components/monitors/AnalysisDialog";
import { SettingsDialog } from "../components/settings/SettingsDialog";
import { useI18n } from "../i18n";
import { Eye, Loader2 } from "lucide-react";

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.97 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: i * 0.06,
      duration: 0.45,
      ease: [0.25, 0.46, 0.45, 0.94] as const,
    },
  }),
};

export function DashboardPage() {
  const { data: projects, isLoading, error } = useProjects();
  const deleteProject = useDeleteProject();
  const createMonitor = useCreateMonitor();
  const { t, locale } = useI18n();
  const [showSettings, setShowSettings] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedTaskUrl, setSelectedTaskUrl] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: taskData } = useTaskPoll(selectedTaskId);
  const taskDone = taskData?.status === "completed" || taskData?.status === "failed";

  useEffect(() => {
    if (!taskDone || !selectedTaskId || dialogOpen) return;
    const timeoutId = window.setTimeout(() => {
      setSelectedTaskId(null);
      setSelectedTaskUrl(null);
    }, 3000);
    return () => window.clearTimeout(timeoutId);
  }, [dialogOpen, selectedTaskId, taskDone]);

  const deleteError =
    deleteProject.error instanceof Error
      ? deleteProject.error.message
      : deleteProject.isError
        ? "Failed to delete project."
        : null;

  if (isLoading) {
    return (
      <AnimatedPage>
        <div className="mb-10">
          <div className="h-8 w-48 rounded-lg bg-slate-100 animate-pulse mb-2" />
          <div className="h-4 w-72 rounded bg-slate-50 animate-pulse" />
        </div>
        <SkeletonCard count={3} />
      </AnimatedPage>
    );
  }
  if (error) return <ErrorAlert message={error.message} />;

  return (
    <AnimatedPage>
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">{t("dashboard.title")}</h1>
        <p className="text-[15px] text-slate-500 mt-1.5">{t("dashboard.subtitle")}</p>
      </div>

      <SetupBanner onOpenSettings={() => setShowSettings(true)} />

      <div className="mb-8">
        <MonitorForm
          onSubmit={async (data) => {
            const result = await createMonitor.mutateAsync({ ...data, locale });
            if (result.task_id) {
              setSelectedTaskId(result.task_id);
              setSelectedTaskUrl(data.url);
              setDialogOpen(true);
            }
          }}
          isLoading={createMonitor.isPending}
        />
        {selectedTaskId && selectedTaskUrl && !dialogOpen && !taskDone && (
          <button
            onClick={() => setDialogOpen(true)}
            className="mt-3 flex w-full items-center gap-3 rounded-xl bg-indigo-50 px-4 py-3 text-sm text-indigo-700 ring-1 ring-inset ring-indigo-200 transition-colors hover:bg-indigo-100"
          >
            <Loader2 size={16} className="animate-spin" />
            <span className="flex-1 truncate text-left">
              {t("monitors.aiAnalyzing")}: {selectedTaskUrl}
            </span>
            <span className="flex items-center gap-1 text-xs font-medium">
              <Eye size={14} />
              {t("monitors.viewDetails")}
            </span>
          </button>
        )}
      </div>

      {deleteError ? <div className="mb-6"><ErrorAlert message={deleteError} /></div> : null}
      <InsightBanner />
      <GlobalOverview />

      {projects?.length ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p, i) => (
            <motion.div
              key={p.id}
              custom={i}
              variants={cardVariants}
              initial="hidden"
              animate="visible"
              whileHover={{
                y: -4,
                transition: { duration: 0.2, ease: "easeOut" },
              }}
            >
              <ProjectCard
                project={p}
                onDelete={(id) => {
                  if (window.confirm(t("dashboard.deleteConfirm"))) {
                    deleteProject.mutate(id);
                  }
                }}
              />
            </motion.div>
          ))}
        </div>
      ) : null}

      {selectedTaskId && dialogOpen && (
        <AnalysisDialog
          taskId={selectedTaskId}
          url={selectedTaskUrl ?? ""}
          onClose={() => setDialogOpen(false)}
        />
      )}
      {showSettings && <SettingsDialog onClose={() => setShowSettings(false)} />}
    </AnimatedPage>
  );
}

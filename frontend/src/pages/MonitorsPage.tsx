import { useState } from "react";
import { useMonitors, useCreateMonitor, useDeleteMonitor } from "../hooks/useMonitors";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { EmptyState } from "../components/common/EmptyState";
import { MonitorList } from "../components/monitors/MonitorList";
import { MonitorForm } from "../components/monitors/MonitorForm";
import { AnalysisDialog } from "../components/monitors/AnalysisDialog";
import { useTaskPoll } from "../hooks/useTasks";
import { useI18n } from "../i18n";
import { Loader2, Eye } from "lucide-react";

export function MonitorsPage() {
  const { data: monitors, isLoading, error } = useMonitors();
  const createMonitor = useCreateMonitor();
  const deleteMonitor = useDeleteMonitor();
  const { t, locale } = useI18n();
  const isZh = locale === "zh";
  const [analysisTask, setAnalysisTask] = useState<{ taskId: string; url: string } | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Poll task to know when it finishes (for the minimized bar)
  const { data: taskData } = useTaskPoll(analysisTask?.taskId ?? null);
  const taskDone = taskData?.status === "completed" || taskData?.status === "failed";

  // Auto-clear finished tasks after 3s
  if (taskDone && analysisTask && !dialogOpen) {
    setTimeout(() => setAnalysisTask(null), 3000);
  }

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error.message} />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">{t("monitors.title")}</h1>
      <MonitorForm
        onSubmit={async (data) => {
          const result = await createMonitor.mutateAsync(data);
          if (result.task_id) {
            setAnalysisTask({ taskId: result.task_id, url: data.url });
            setDialogOpen(true);
          }
        }}
        isLoading={createMonitor.isPending}
      />

      {/* Minimized analysis bar — shown when dialog is closed but task is still running */}
      {analysisTask && !dialogOpen && !taskDone && (
        <button
          onClick={() => setDialogOpen(true)}
          className="flex w-full items-center gap-3 rounded-xl bg-indigo-50 px-4 py-3 text-sm text-indigo-700 ring-1 ring-inset ring-indigo-200 transition-colors hover:bg-indigo-100"
        >
          <Loader2 size={16} className="animate-spin" />
          <span className="flex-1 truncate text-left">
            {isZh ? "AI 正在分析" : "AI analyzing"}: {analysisTask.url}
          </span>
          <span className="flex items-center gap-1 text-xs font-medium">
            <Eye size={14} />
            {isZh ? "查看详情" : "View details"}
          </span>
        </button>
      )}

      {!monitors?.length ? (
        <EmptyState
          title={t("monitors.noMonitors")}
          description={t("monitors.noMonitorsDesc")}
        />
      ) : (
        <MonitorList
          monitors={monitors}
          onDelete={(id) => deleteMonitor.mutate(id)}
        />
      )}

      {analysisTask && dialogOpen && (
        <AnalysisDialog
          taskId={analysisTask.taskId}
          url={analysisTask.url}
          onClose={() => setDialogOpen(false)}
        />
      )}
    </div>
  );
}

import { useState } from "react";
import { Play, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { useRunMonitor } from "../../hooks/useMonitors";
import { useTaskPoll } from "../../hooks/useTasks";
import { useQueryClient } from "@tanstack/react-query";
import { useI18n } from "../../i18n";

export function RunScanButton({
  monitorId,
  projectId,
}: {
  monitorId: number;
  projectId: number;
}) {
  const [taskId, setTaskId] = useState<string | null>(null);
  const runMonitor = useRunMonitor();
  const { data: task } = useTaskPoll(taskId);
  const qc = useQueryClient();
  const { t } = useI18n();

  const status = task?.status;

  // Reset after completion
  if (status === "completed" || status === "failed") {
    if (status === "completed") {
      qc.invalidateQueries({ queryKey: ["project-summary", projectId] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    }
  }

  const handleRun = async () => {
    try {
      const record = await runMonitor.mutateAsync(monitorId);
      setTaskId(record.task_id);
    } catch {
      // 409 or other error handled by mutation
    }
  };

  if (status === "running" || status === "pending") {
    return (
      <span className="flex items-center gap-1.5 rounded-lg bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-600">
        <Loader2 size={14} className="animate-spin" />
        {t("runScan.running")}
      </span>
    );
  }

  if (status === "completed") {
    return (
      <span className="flex items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-600">
        <CheckCircle size={14} />
        {t("runScan.done")}
      </span>
    );
  }

  if (status === "failed") {
    return (
      <span className="flex items-center gap-1.5 rounded-lg bg-rose-50 px-3 py-1.5 text-xs font-medium text-rose-600" title={task?.error ?? ""}>
        <XCircle size={14} />
        {t("runScan.failed")}
      </span>
    );
  }

  return (
    <button
      onClick={handleRun}
      disabled={runMonitor.isPending}
      className="flex items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 transition-colors hover:bg-emerald-100 disabled:opacity-50"
    >
      <Play size={12} />
      {t("runScan.run")}
    </button>
  );
}

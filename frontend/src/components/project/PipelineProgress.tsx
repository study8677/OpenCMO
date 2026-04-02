import { useState, useEffect, useRef } from "react";
import {
  CheckCircle, Circle, Loader2, XCircle, ChevronDown,
} from "lucide-react";
import { useTaskPoll } from "../../hooks/useTasks";
import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";
import type { TaskProgressEntry } from "../../types";

const PHASE_LABEL_KEYS: Record<string, TranslationKey> = {
  reflection: "pipeline.phaseReflection",
  distillation: "pipeline.phaseDistillation",
  planning: "pipeline.phasePlanning",
  writing: "pipeline.phaseWriting",
  grading: "pipeline.phaseGrading",
  synthesis: "pipeline.phaseSynthesis",
};

const PHASE_ORDER = ["reflection", "distillation", "planning", "writing", "grading", "synthesis"];

function PhaseIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle size={18} className="text-emerald-500" />;
  if (status === "running") return <Loader2 size={18} className="text-blue-500 animate-spin" />;
  if (status === "failed") return <XCircle size={18} className="text-rose-500" />;
  return <Circle size={18} className="text-slate-300" />;
}

export function PipelineProgress({
  taskId,
  onComplete,
}: {
  taskId: string;
  onComplete?: () => void;
}) {
  const [expandedPhaseIdx, setExpandedPhaseIdx] = useState<number | null>(null);
  const { t } = useI18n();
  const completedRef = useRef(false);
  const { data: task, isLoading } = useTaskPoll(taskId);

  useEffect(() => {
    if (!task) return;
    if ((task.status === "completed" || task.status === "failed") && !completedRef.current) {
      completedRef.current = true;
      if (task.status === "completed" && onComplete) {
        setTimeout(onComplete, 1500);
      }
    }
  }, [task, onComplete]);

  if (isLoading || !task) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 size={20} className="animate-spin text-slate-400" />
        <span className="ml-2 text-sm text-slate-500">{t("pipeline.connecting")}</span>
      </div>
    );
  }

  // Build phase status map from progress events
  const phaseStatus: Record<string, { status: string; events: TaskProgressEntry[] }> = {};
  for (const event of task.progress) {
    const phase = event.phase;
    if (!phase) continue;
    if (!phaseStatus[phase]) {
      phaseStatus[phase] = { status: event.status ?? "running", events: [] };
    }
    phaseStatus[phase].status = event.status ?? phaseStatus[phase].status;
    phaseStatus[phase].events.push(event);
  }

  // Determine overall progress
  const completedPhases = PHASE_ORDER.filter((p) => phaseStatus[p]?.status === "completed").length;
  const progressPercent = task.status === "completed" ? 100 : Math.round((completedPhases / PHASE_ORDER.length) * 100);

  return (
    <div className="rounded-2xl border border-slate-200/70 bg-gradient-to-b from-white to-slate-50/80 p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {task.status === "running" && (
            <div className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-blue-500" />
            </div>
          )}
          {task.status === "completed" && <CheckCircle size={16} className="text-emerald-500" />}
          {task.status === "failed" && <XCircle size={16} className="text-rose-500" />}
          <span className="text-sm font-semibold text-slate-700">
            {task.status === "pending" && t("pipeline.preparing")}
            {task.status === "running" && t("pipeline.agentsWorking")}
            {task.status === "completed" && t("pipeline.complete")}
            {task.status === "failed" && t("pipeline.error")}
          </span>
        </div>
        <span className="text-xs font-medium text-slate-500">
          {progressPercent}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 w-full rounded-full bg-slate-100 mb-5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${
            task.status === "failed" ? "bg-rose-500" :
            task.status === "completed" ? "bg-emerald-500" : "bg-blue-500"
          }`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Phase Timeline */}
      <div className="space-y-1">
        {PHASE_ORDER.map((phaseId, idx) => {
          const phase = phaseStatus[phaseId];
          const status = phase?.status || "pending";
          const labelKey = PHASE_LABEL_KEYS[phaseId];
          const label = labelKey ? t(labelKey) : phaseId;
          const events = phase?.events || [];
          const latestEvent = events[events.length - 1];
          const isExpanded = expandedPhaseIdx === idx;

          return (
            <div key={phaseId}>
              <button
                type="button"
                onClick={() => setExpandedPhaseIdx(isExpanded ? null : idx)}
                className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition hover:bg-slate-50"
              >
                {/* Timeline connector */}
                <div className="flex flex-col items-center">
                  <PhaseIcon status={status} />
                  {idx < PHASE_ORDER.length - 1 && (
                    <div className={`mt-1 h-3 w-px ${
                      status === "completed" ? "bg-emerald-300" : "bg-slate-200"
                    }`} />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <span className={`text-sm font-medium ${
                    status === "completed" ? "text-emerald-700" :
                    status === "running" ? "text-blue-700" :
                    status === "failed" ? "text-rose-700" : "text-slate-400"
                  }`}>
                    {label}
                  </span>
                  {latestEvent && status !== "pending" && (
                    <p className="text-xs text-slate-500 truncate mt-0.5">
                      {latestEvent.summary}
                    </p>
                  )}
                </div>

                {events.length > 1 && (
                  <ChevronDown size={14} className={`text-slate-400 transition ${isExpanded ? "rotate-180" : ""}`} />
                )}
              </button>

              {/* Expanded sub-events */}
              {isExpanded && events.length > 1 && (
                <div className="ml-[42px] mb-2 space-y-1 animate-in fade-in slide-in-from-top-1 duration-200">
                  {events.map((evt, i) => (
                    <div key={i} className="flex items-start gap-2 rounded-lg bg-slate-50 px-3 py-1.5">
                      <span className={`mt-0.5 h-1.5 w-1.5 rounded-full shrink-0 ${
                        evt.status === "completed" ? "bg-emerald-400" :
                        evt.status === "running" ? "bg-blue-400" :
                        evt.status === "failed" ? "bg-rose-400" : "bg-slate-300"
                      }`} />
                      <span className="text-xs text-slate-600 leading-snug">
                        {evt.summary}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Error display */}
      {task.error && (
        <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3">
          <p className="text-xs font-medium text-rose-800">{task.error}</p>
        </div>
      )}
    </div>
  );
}

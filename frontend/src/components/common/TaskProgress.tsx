import { useMemo } from "react";
import { CheckCircle2, Loader2, AlertCircle, ChevronRight } from "lucide-react";
import type { TaskEvent } from "../../hooks/useTaskEvents";

interface TaskProgressProps {
  events: TaskEvent[];
  isStreaming: boolean;
}

interface PhaseStep {
  stage: string;
  agent: string;
  summary: string;
  status: "completed" | "running" | "failed" | "pending";
}

const STAGE_LABELS: Record<string, string> = {
  context_build: "Context Analysis",
  signal_collect: "Signal Collection",
  signal_normalize: "Signal Processing",
  domain_review: "Domain Review",
  strategy_synthesis: "Strategy Synthesis",
  persist_publish: "Saving Results",
  reporting: "Report Generation",
};

function StepIcon({ status }: { status: string }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />;
    case "running":
      return <Loader2 className="h-4 w-4 text-brand-500 animate-spin shrink-0" />;
    case "failed":
      return <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />;
    default:
      return <div className="h-4 w-4 rounded-full border-2 border-slate-200 shrink-0" />;
  }
}

export function TaskProgress({ events, isStreaming }: TaskProgressProps) {
  const steps = useMemo(() => {
    const result: PhaseStep[] = [];
    const seen = new Set<string>();

    for (const ev of events) {
      if (ev.type !== "progress") continue;
      const key = `${ev.stage}-${ev.agent}`;
      if (seen.has(key)) {
        // Update existing step
        const existing = result.find(
          (s) => s.stage === ev.stage && s.agent === (ev.agent ?? ""),
        );
        if (existing) {
          existing.status = (ev.status as PhaseStep["status"]) ?? "running";
          existing.summary = ev.summary ?? existing.summary;
        }
        continue;
      }
      seen.add(key);
      result.push({
        stage: ev.stage ?? "unknown",
        agent: ev.agent ?? "",
        summary: ev.summary ?? "",
        status: (ev.status as PhaseStep["status"]) ?? "running",
      });
    }
    return result;
  }, [events]);

  const doneEvent = events.find((e) => e.type === "done");

  if (steps.length === 0 && !isStreaming) return null;

  return (
    <div className="rounded-xl border border-slate-100 bg-white shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 py-3 border-b border-slate-50 bg-slate-50/50">
        {isStreaming ? (
          <Loader2 className="h-4 w-4 text-brand-500 animate-spin" />
        ) : doneEvent?.status === "completed" ? (
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
        ) : (
          <AlertCircle className="h-4 w-4 text-red-500" />
        )}
        <span className="text-sm font-semibold text-slate-700">
          {isStreaming
            ? "Scan in progress…"
            : doneEvent?.status === "completed"
              ? "Scan complete"
              : "Scan finished with errors"}
        </span>
        {doneEvent && (
          <span className="ml-auto text-xs text-slate-400">
            {doneEvent.findings_count ?? 0} findings · {doneEvent.recommendations_count ?? 0} actions
          </span>
        )}
      </div>

      {/* Steps */}
      <div className="px-4 py-3 space-y-2">
        {steps.map((step, i) => (
          <div
            key={`${step.stage}-${step.agent}-${i}`}
            className="flex items-start gap-2.5 group"
          >
            <div className="mt-0.5">
              <StepIcon status={step.status} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-medium text-slate-500">
                  {STAGE_LABELS[step.stage] ?? step.stage}
                </span>
                {step.agent && (
                  <>
                    <ChevronRight className="h-3 w-3 text-slate-300" />
                    <span className="text-xs font-medium text-brand-600">
                      {step.agent}
                    </span>
                  </>
                )}
              </div>
              <p className="text-xs text-slate-500 leading-relaxed mt-0.5 line-clamp-2">
                {step.summary}
              </p>
            </div>
          </div>
        ))}

        {isStreaming && steps.length === 0 && (
          <div className="flex items-center gap-2 text-slate-400 py-2">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span className="text-xs">Initializing scan…</span>
          </div>
        )}
      </div>
    </div>
  );
}

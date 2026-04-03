import { useEffect, useMemo } from "react";
import {
  X,
  Search,
  BarChart3,
  MessageCircle,
  Target,
  Bot,
  Loader2,
  CheckCircle,
  Radar,
  TriangleAlert,
  Lightbulb,
} from "lucide-react";
import { useTaskPoll, useTaskFindings, useTaskRecommendations } from "../../hooks/useTasks";
import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";
import type { AnalysisProgress } from "../../types";

const STAGE_CONFIG: Record<string, { icon: typeof Search; labelKey: TranslationKey }> = {
  context_build: { icon: Search, labelKey: "analysis.stageContextBuild" },
  signal_collect: { icon: Radar, labelKey: "analysis.stageSignalCollect" },
  signal_normalize: { icon: Bot, labelKey: "analysis.stageSignalNormalize" },
  domain_review: { icon: MessageCircle, labelKey: "analysis.stageDomainReview" },
  strategy_synthesis: { icon: Target, labelKey: "analysis.stageStrategySynthesis" },
  persist_publish: { icon: CheckCircle, labelKey: "analysis.stagePersistPublish" },
};

const STATUS_STYLE: Record<string, string> = {
  started: "bg-slate-50 text-slate-600 ring-slate-200",
  running: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  failed: "bg-rose-50 text-rose-700 ring-rose-200",
};

function getLatestStageEvents(progress: AnalysisProgress[]) {
  const byStage = new Map<string, AnalysisProgress>();
  for (const item of progress) {
    if (!item.stage) continue;
    byStage.set(item.stage, item);
  }
  return [...byStage.entries()];
}

function getAnalystEvents(progress: AnalysisProgress[]) {
  return progress.filter((item) => item.stage === "domain_review" && item.agent);
}

export function AnalysisDialog({
  taskId,
  url,
  onClose,
}: {
  taskId: string;
  url: string;
  onClose: () => void;
}) {
  const { data: task } = useTaskPoll(taskId);
  const { t } = useI18n();

  const progress: AnalysisProgress[] = task?.progress ?? [];
  const isDone = task?.status === "completed" || task?.status === "failed";
  const latestStageEvents = useMemo(() => getLatestStageEvents(progress), [progress]);
  const analystEvents = useMemo(() => getAnalystEvents(progress), [progress]);

  const { data: findings = [] } = useTaskFindings(taskId, isDone);
  const { data: recommendations = [] } = useTaskRecommendations(taskId, isDone);

  useEffect(() => {
    const el = document.getElementById("analysis-scroll");
    if (el) el.scrollTop = el.scrollHeight;
  }, [progress.length, findings.length, recommendations.length]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="flex h-[82vh] w-full max-w-3xl flex-col rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              {t("analysis.title")}
            </h2>
            <p className="mt-0.5 max-w-xl truncate text-xs text-slate-400">{url}</p>
            <p className="mt-0.5 text-xs text-slate-400">
              {t("analysis.backgroundHint")}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        <div id="analysis-scroll" className="flex-1 space-y-6 overflow-y-auto px-6 py-4">
          {progress.length === 0 && !isDone && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Loader2 size={32} className="mb-3 animate-spin text-indigo-400" />
              <p className="text-sm text-slate-400">
                {t("analysis.initializing")}
              </p>
            </div>
          )}

          {latestStageEvents.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <div className="h-px flex-1 bg-slate-100" />
                <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                  {t("analysis.workflowStages")}
                </span>
                <div className="h-px flex-1 bg-slate-100" />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {latestStageEvents.map(([stage, item]) => {
                  const cfg = STAGE_CONFIG[stage] ?? STAGE_CONFIG.context_build!;
                  const Icon = cfg.icon;
                  const style = STATUS_STYLE[item.status ?? "started"] ?? STATUS_STYLE.started;
                  return (
                    <div key={stage} className={`rounded-xl p-4 ring-1 ring-inset ${style}`}>
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <Icon size={14} />
                          <span className="text-xs font-semibold">
                            {t(cfg.labelKey)}
                          </span>
                        </div>
                        <span className="text-[10px] font-semibold uppercase tracking-wider opacity-80">
                          {item.status ?? "started"}
                        </span>
                      </div>
                      <p className="text-sm leading-relaxed">
                        {item.summary ?? item.detail ?? item.content}
                      </p>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {analystEvents.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <div className="h-px flex-1 bg-slate-100" />
                <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                  {t("analysis.domainReviews")}
                </span>
                <div className="h-px flex-1 bg-slate-100" />
              </div>
              <div className="space-y-3">
                {analystEvents.map((item, index) => (
                  <div key={`${item.agent}-${index}`} className="rounded-xl bg-slate-50 p-4 ring-1 ring-inset ring-slate-200">
                    <div className="mb-1.5 flex items-center gap-2">
                      <BarChart3 size={14} className="text-slate-500" />
                      <span className="text-xs font-semibold text-slate-700">{item.agent}</span>
                    </div>
                    <p className="text-sm leading-relaxed text-slate-700">
                      {item.detail ?? item.summary ?? item.content}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {isDone && findings.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <TriangleAlert size={14} className="text-rose-500" />
                <h3 className="text-sm font-semibold text-slate-900">
                  {t("analysis.keyFindings")}
                </h3>
              </div>
              <div className="space-y-3">
                {findings.map((finding, index) => (
                  <div key={`${finding.domain}-${finding.title}-${index}`} className="rounded-xl border border-slate-200 bg-white p-4">
                    <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      <span>{finding.domain}</span>
                      <span>•</span>
                      <span>{finding.severity}</span>
                    </div>
                    <p className="text-sm font-semibold text-slate-900">{finding.title}</p>
                    <p className="mt-1 text-sm leading-relaxed text-slate-600">{finding.summary}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {isDone && recommendations.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <Lightbulb size={14} className="text-amber-500" />
                <h3 className="text-sm font-semibold text-slate-900">
                  {t("analysis.recommendedActions")}
                </h3>
              </div>
              <div className="space-y-3">
                {recommendations.map((rec, index) => (
                  <div key={`${rec.domain}-${rec.title}-${index}`} className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-4">
                    <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-500">
                      <span>{rec.priority}</span>
                      <span>•</span>
                      <span>{rec.owner_type}</span>
                    </div>
                    <p className="text-sm font-semibold text-slate-900">{rec.title}</p>
                    <p className="mt-1 text-sm leading-relaxed text-slate-600">{rec.summary}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {task?.summary && (
            <div className={`rounded-xl px-4 py-3 text-sm ring-1 ring-inset ${
              task.status === "failed"
                ? "bg-rose-50 text-rose-700 ring-rose-200"
                : "bg-slate-50 text-slate-700 ring-slate-200"
            }`}>
              {task.summary}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 px-6 py-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            {isDone ? (
              <>
                <CheckCircle size={14} className={task?.status === "failed" ? "text-rose-500" : "text-emerald-500"} />
                <span className={task?.status === "failed" ? "text-rose-600" : "text-emerald-600"}>
                  {task?.status === "failed"
                    ? t("analysis.workflowFailed")
                    : t("analysis.workflowComplete")}
                </span>
              </>
            ) : (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>
                  {latestStageEvents.length}
                  {" / 6 "}
                  {t("analysis.stages")}
                </span>
              </>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-xl bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100"
          >
            {isDone ? t("analysis.close") : t("analysis.closeBackground")}
          </button>
        </div>
      </div>
    </div>
  );
}

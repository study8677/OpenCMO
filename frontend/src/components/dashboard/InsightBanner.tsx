import { useState } from "react";
import { ChevronRight, X } from "lucide-react";
import { useNavigate } from "react-router";
import type { InsightActionParams, InsightRecord, InsightSeverity } from "../../api/insights";
import { useInsights, useMarkInsightRead } from "../../hooks/useInsights";
import { useI18n } from "../../i18n";

function getInsightRoute(actionParams: InsightActionParams): string | null {
  return typeof actionParams.route === "string" && actionParams.route.length > 0
    ? actionParams.route
    : null;
}

function getSeverityStyles(severity: InsightSeverity) {
  switch (severity) {
    case "critical":
      return {
        border: "border-l-rose-500",
        badge: "bg-rose-50 text-rose-700 ring-rose-200/80",
        button: "bg-rose-500 text-white hover:bg-rose-400 shadow-[0_14px_36px_rgba(244,63,94,0.24)]",
      };
    case "warning":
      return {
        border: "border-l-amber-500",
        badge: "bg-amber-50 text-amber-700 ring-amber-200/80",
        button: "bg-amber-500 text-white hover:bg-amber-400 shadow-[0_14px_36px_rgba(245,158,11,0.22)]",
      };
    default:
      return {
        border: "border-l-sky-500",
        badge: "bg-sky-50 text-sky-700 ring-sky-200/80",
        button: "bg-sky-500 text-white hover:bg-sky-400 shadow-[0_14px_36px_rgba(14,165,233,0.22)]",
      };
  }
}

export function InsightBanner() {
  const [dismissedIds, setDismissedIds] = useState<number[]>([]);
  const navigate = useNavigate();
  const { t } = useI18n();
  const { data: insights } = useInsights(undefined, true);
  const markInsightRead = useMarkInsightRead();

  const visibleInsights = (insights ?? [])
    .filter((insight) => !dismissedIds.includes(insight.id))
    .slice(0, 2);

  if (visibleInsights.length === 0) {
    return null;
  }

  async function handleDismiss(insightId: number) {
    setDismissedIds((current) => [...current, insightId]);

    try {
      await markInsightRead.mutateAsync(insightId);
    } catch {
      setDismissedIds((current) => current.filter((id) => id !== insightId));
    }
  }

  async function handleView(insight: InsightRecord) {
    const route = getInsightRoute(insight.action_params);

    if (!route) {
      return;
    }

    try {
      await markInsightRead.mutateAsync(insight.id);
    } catch {
      // Navigation is still useful even if marking as read fails.
    } finally {
      navigate(route);
    }
  }

  return (
    <section className="mb-8 rounded-[1.75rem] border border-slate-200/70 bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.1),_transparent_35%),linear-gradient(180deg,rgba(255,255,255,0.96),rgba(248,250,252,0.94))] p-5 shadow-[0_18px_50px_rgba(15,23,42,0.08)] backdrop-blur-xl ring-1 ring-white/50 sm:p-6">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-sky-600/80">
            {t("insights.proactive")}
          </p>
          <h2 className="mt-1 text-lg font-semibold tracking-tight text-slate-900">
            {t("insights.topUnread")}
          </h2>
        </div>
        <span className="w-fit rounded-full bg-slate-900 px-2.5 py-1 text-[11px] font-semibold text-white">
          {visibleInsights.length}
        </span>
      </div>

      <div className="space-y-3">
        {visibleInsights.map((insight) => {
          const severity = getSeverityStyles(insight.severity);
          const route = getInsightRoute(insight.action_params);

          return (
            <article
              key={insight.id}
              className={`rounded-[1.5rem] border border-slate-200/70 border-l-4 bg-white/85 p-4 shadow-sm backdrop-blur-sm ${severity.border}`}
            >
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ring-1 ${severity.badge}`}>
                      {insight.severity}
                    </span>
                    <span className="text-[11px] font-medium text-slate-400">
                      #{insight.project_id}
                    </span>
                  </div>
                  <h3 className="mt-3 text-base font-semibold text-slate-900">
                    {insight.title}
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    {insight.summary}
                  </p>
                </div>

                <div className="flex items-center gap-2 self-start">
                  <button
                    type="button"
                    disabled={!route}
                    onClick={() => {
                      void handleView(insight);
                    }}
                    className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50 ${severity.button}`}
                  >
                    {t("insights.view")}
                    <ChevronRight size={15} />
                  </button>
                  <button
                    type="button"
                    title={t("insights.dismiss")}
                    aria-label={t("insights.dismiss")}
                    onClick={() => {
                      void handleDismiss(insight.id);
                    }}
                    className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200/80 bg-white/80 text-slate-400 transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:text-slate-700 active:scale-95"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

import { useEffect, useRef, useState } from "react";
import { Bell, ChevronRight, Loader2 } from "lucide-react";
import { useLocation, useNavigate } from "react-router";
import type { InsightActionParams, InsightSeverity, InsightSummaryItem } from "../../api/insights";
import { useInsightsSummary, useMarkInsightRead } from "../../hooks/useInsights";
import { useI18n } from "../../i18n";

function getSeverityStyles(severity: InsightSeverity) {
  switch (severity) {
    case "critical":
      return {
        dot: "bg-rose-500",
        badge: "bg-rose-50 text-rose-700 ring-rose-200/80",
      };
    case "warning":
      return {
        dot: "bg-amber-500",
        badge: "bg-amber-50 text-amber-700 ring-amber-200/80",
      };
    default:
      return {
        dot: "bg-sky-500",
        badge: "bg-sky-50 text-sky-700 ring-sky-200/80",
      };
  }
}

function getInsightRoute(actionParams: InsightActionParams): string | null {
  return typeof actionParams.route === "string" && actionParams.route.length > 0
    ? actionParams.route
    : null;
}

function formatTimeAgo(value: string, locale: "en" | "zh") {
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) {
    return "";
  }

  const diffSeconds = Math.round((timestamp - Date.now()) / 1000);
  const absSeconds = Math.abs(diffSeconds);
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });

  if (absSeconds < 60) return rtf.format(diffSeconds, "second");

  const diffMinutes = Math.round(diffSeconds / 60);
  if (Math.abs(diffMinutes) < 60) return rtf.format(diffMinutes, "minute");

  const diffHours = Math.round(diffMinutes / 60);
  if (Math.abs(diffHours) < 24) return rtf.format(diffHours, "hour");

  const diffDays = Math.round(diffHours / 24);
  if (Math.abs(diffDays) < 7) return rtf.format(diffDays, "day");

  const diffWeeks = Math.round(diffDays / 7);
  if (Math.abs(diffWeeks) < 4) return rtf.format(diffWeeks, "week");

  const diffMonths = Math.round(diffDays / 30);
  if (Math.abs(diffMonths) < 12) return rtf.format(diffMonths, "month");

  const diffYears = Math.round(diffDays / 365);
  return rtf.format(diffYears, "year");
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { locale, t } = useI18n();
  const { data, isLoading } = useInsightsSummary();
  const markInsightRead = useMarkInsightRead();

  const recentInsights = data?.recent ?? [];
  const unreadCount = data?.unread_count ?? 0;

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (
        containerRef.current &&
        event.target instanceof Node &&
        !containerRef.current.contains(event.target)
      ) {
        setOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  async function handleSelect(insight: InsightSummaryItem) {
    const route = getInsightRoute(insight.action_params);

    setOpen(false);

    try {
      await markInsightRead.mutateAsync(insight.id);
    } catch {
      // Let cache invalidation and the next poll reconcile the bell if the request fails.
    } finally {
      if (route) {
        navigate(route);
      }
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        title={t("insights.title")}
        aria-label={t("insights.title")}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((current) => !current)}
        className="group relative flex h-10 w-10 items-center justify-center rounded-xl border border-white/50 bg-white/70 text-slate-500 shadow-sm backdrop-blur-xl transition-all duration-200 hover:-translate-y-0.5 hover:bg-white hover:text-slate-900 hover:shadow-md active:scale-95"
      >
        <Bell size={18} className="transition-transform duration-200 group-hover:-rotate-6" />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex min-h-5 min-w-5 items-center justify-center rounded-full bg-rose-500 px-1.5 text-[10px] font-semibold text-white shadow-[0_10px_24px_rgba(244,63,94,0.35)]">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-[calc(100%+0.75rem)] z-40 w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-[1.5rem] border border-white/60 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(248,250,252,0.92))] p-3 shadow-[0_24px_60px_rgba(15,23,42,0.16)] backdrop-blur-2xl ring-1 ring-slate-950/5">
          <div className="mb-2 flex items-center justify-between px-2 py-1">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                {t("insights.proactive")}
              </p>
              <h3 className="text-sm font-semibold text-slate-900">{t("insights.title")}</h3>
            </div>
            {unreadCount > 0 && (
              <span className="rounded-full bg-slate-900 px-2.5 py-1 text-[11px] font-semibold text-white">
                {unreadCount}
              </span>
            )}
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center gap-2 px-4 py-8 text-sm text-slate-500">
              <Loader2 size={16} className="animate-spin" />
              {t("insights.loading")}
            </div>
          ) : recentInsights.length > 0 ? (
            <div className="space-y-2">
              {recentInsights.map((insight) => {
                const severity = getSeverityStyles(insight.severity);

                return (
                  <button
                    key={insight.id}
                    type="button"
                    onClick={() => {
                      void handleSelect(insight);
                    }}
                    className="group flex w-full items-start gap-3 rounded-[1.25rem] border border-white/60 bg-white/75 px-4 py-3 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-white hover:shadow-md"
                  >
                    <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${severity.dot}`} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-slate-900">{insight.title}</p>
                          <div className="mt-1 flex items-center gap-2">
                            <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] ring-1 ${severity.badge}`}>
                              {insight.severity}
                            </span>
                            <span className="text-[11px] text-slate-400">
                              {formatTimeAgo(insight.created_at, locale)}
                            </span>
                          </div>
                        </div>
                        <ChevronRight size={16} className="mt-0.5 shrink-0 text-slate-300 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-slate-500" />
                      </div>
                      <p className="mt-2 text-xs leading-5 text-slate-500">{insight.summary}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="rounded-[1.25rem] border border-dashed border-slate-200/80 bg-white/60 px-4 py-8 text-center text-sm text-slate-500">
              {t("insights.empty")}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

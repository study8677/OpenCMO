import { useMemo, useState } from "react";
import { ChevronDown, Loader2, TriangleAlert, Lightbulb } from "lucide-react";
import { useMonitorRuns } from "../../hooks/useMonitors";
import { useI18n, type TranslationKey } from "../../i18n";
import { RunResultsDialog } from "./RunResultsDialog";
import type { MonitorRun } from "../../types";

const STATUS_STYLE: Record<MonitorRun["status"], string> = {
  pending: "bg-amber-50 text-amber-700 ring-amber-200/80",
  running: "bg-indigo-50 text-indigo-700 ring-indigo-200/80",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-200/80",
  failed: "bg-rose-50 text-rose-700 ring-rose-200/80",
};

const STATUS_LABELS: Record<MonitorRun["status"], TranslationKey> = {
  pending: "runHistory.status.pending",
  running: "runHistory.status.running",
  completed: "runHistory.status.completed",
  failed: "runHistory.status.failed",
};

import { utcDate } from "../../utils/time";

function formatTimeAgo(value: string, locale: string) {
  const timestamp = utcDate(value).getTime();
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

function formatAbsoluteTime(value: string, locale: string) {
  const date = utcDate(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(locale === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function RunHistoryPanel({
  monitorId,
  url,
}: {
  monitorId: number;
  url: string;
}) {
  const { data: runs = [], isLoading } = useMonitorRuns(monitorId);
  const { t, locale } = useI18n();
  const [open, setOpen] = useState(false);
  const [selectedRun, setSelectedRun] = useState<MonitorRun | null>(null);

  const recentRuns = useMemo(
    () =>
      [...runs]
        .sort((a, b) => utcDate(b.created_at).getTime() - utcDate(a.created_at).getTime())
        .slice(0, 5),
    [runs],
  );

  return (
    <>
      <div className="mt-4 rounded-2xl border border-white/60 bg-[linear-gradient(180deg,rgba(255,255,255,0.82),rgba(248,250,252,0.92))] p-3 shadow-[0_12px_30px_rgba(15,23,42,0.06)] backdrop-blur-xl ring-1 ring-slate-950/5">
        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          className="flex w-full items-center justify-between gap-3 text-left"
        >
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            {t("runHistory.title")}
          </span>
          <ChevronDown
            size={16}
            className={`text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
          />
        </button>

        {open && (
          <div className="mt-3 space-y-2">
            {isLoading ? (
              <div className="flex items-center gap-2 rounded-xl bg-white/70 px-3 py-3 text-xs text-slate-500 ring-1 ring-slate-200/70">
                <Loader2 size={14} className="animate-spin" />
                {t("runHistory.loading")}
              </div>
            ) : recentRuns.length === 0 ? (
              <div className="rounded-xl bg-white/70 px-3 py-3 text-xs text-slate-500 ring-1 ring-slate-200/70">
                {t("runHistory.empty")}
              </div>
            ) : (
              recentRuns.map((run) => {
                const displayTime = run.completed_at ?? run.created_at;
                return (
                  <button
                    key={run.id}
                    type="button"
                    onClick={() => setSelectedRun(run)}
                    title={formatAbsoluteTime(displayTime, locale)}
                    className="w-full rounded-xl bg-white/80 px-3 py-3 text-left ring-1 ring-slate-200/70 transition-all hover:-translate-y-0.5 hover:bg-white hover:shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-800">
                          {formatTimeAgo(displayTime, locale)}
                        </p>
                        <p className="mt-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                          {run.job_type}
                        </p>
                      </div>
                      <span
                        className={`shrink-0 rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wider ring-1 ring-inset ${
                          STATUS_STYLE[run.status]
                        }`}
                      >
                        {t(STATUS_LABELS[run.status])}
                      </span>
                    </div>

                    <div className="mt-2 flex items-center gap-3 text-[11px] text-slate-500">
                      <span
                        className="flex items-center gap-1.5"
                        title={`${run.findings_count} ${t("runHistory.findings")}`}
                      >
                        <TriangleAlert size={12} className="text-rose-400" />
                        {run.findings_count}
                      </span>
                      <span
                        className="flex items-center gap-1.5"
                        title={`${run.recommendations_count} ${t("runHistory.recommendations")}`}
                      >
                        <Lightbulb size={12} className="text-amber-400" />
                        {run.recommendations_count}
                      </span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        )}
      </div>

      {selectedRun && (
        <RunResultsDialog
          run={selectedRun}
          url={url}
          onClose={() => setSelectedRun(null)}
        />
      )}
    </>
  );
}

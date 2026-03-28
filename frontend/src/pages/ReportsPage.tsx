import { useMemo, type ElementType, type ReactNode } from "react";
import { useParams } from "react-router";
import ReactMarkdown from "react-markdown";
import { Bot, FileText, History, Mail, RefreshCcw, User, Download } from "lucide-react";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { useProjectSummary } from "../hooks/useProject";
import { useLatestReports, useRegenerateReport, useReports, useSendReport } from "../hooks/useReports";
import type { ReportKind, ReportRecord } from "../types";
import { useI18n } from "../i18n";
import { downloadAsPDF } from "../utils/pdf";

function formatStamp(value: string | null | undefined) {
  if (!value) return "N/A";
  return value.replace("T", " ").slice(0, 16);
}

function ReportCard({
  label,
  icon,
  report,
  allowDownload,
}: {
  label: string;
  icon: ElementType;
  report: ReportRecord | null;
  allowDownload?: boolean;
}) {
  const Icon = icon;

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-slate-100 p-2 text-slate-600">
            <Icon className="h-4 w-4" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-900">{label}</div>
            {report ? (
              <div className="text-xs text-slate-500">
                v{report.version} · {formatStamp(report.created_at)}
              </div>
            ) : null}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {report?.meta?.low_sample ? (
            <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-700">
              Low Sample
            </span>
          ) : null}
          {allowDownload && report ? (
            <button
              type="button"
              onClick={() =>
                downloadAsPDF({
                  elementId: `report-content-${report.id}`,
                  filename: `OpenCMO-${label.replace(/\s+/g, "-")}-v${report.version}.pdf`,
                  title: `${label} (v${report.version})`
                })
              }
              className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none"
              title="Download PDF"
            >
              <Download className="h-4 w-4" />
            </button>
          ) : null}
        </div>
      </div>

      {report ? (
        <div id={`report-content-${report.id}`} className="prose prose-sm prose-slate max-w-none">
           <ReactMarkdown>{report.content}</ReactMarkdown>
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-500">
          No report generated yet.
        </div>
      )}
    </div>
  );
}

function ReportHistory({ title, reports }: { title: string; reports: ReportRecord[] }) {
  if (!reports.length) return null;

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900">
        <History className="h-4 w-4 text-slate-500" />
        {title}
      </div>
      <div className="space-y-3">
        {reports.map((report) => (
          <details
            key={report.id}
            className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3"
          >
            <summary className="cursor-pointer list-none">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-semibold text-slate-900">
                  v{report.version} · {report.audience}
                </span>
                {report.is_latest ? (
                  <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-700">
                    Latest
                  </span>
                ) : null}
                <span className="text-slate-500">{formatStamp(report.created_at)}</span>
              </div>
            </summary>
            <div className="prose prose-sm prose-slate mt-4 max-w-none">
              <ReactMarkdown>{report.content}</ReactMarkdown>
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}

function ReportSection({
  title,
  description,
  kind,
  human,
  agent,
  onRegenerate,
  regenerating,
  extraAction,
}: {
  title: string;
  description: string;
  kind: ReportKind;
  human: ReportRecord | null;
  agent: ReportRecord | null;
  onRegenerate: (kind: ReportKind) => void;
  regenerating: boolean;
  extraAction?: ReactNode;
}) {
  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 rounded-3xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-6 shadow-sm lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
          <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-500">{description}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => onRegenerate(kind)}
            disabled={regenerating}
            className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCcw className={`h-4 w-4 ${regenerating ? "animate-spin" : ""}`} />
            {kind === "strategic" ? "Regenerate Strategic" : "Regenerate Weekly"}
          </button>
          {extraAction}
        </div>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <ReportCard label="Human Readout" icon={User} report={human} allowDownload />
        <ReportCard label="Agent Brief" icon={Bot} report={agent} />
      </div>
    </section>
  );
}

export function ReportsPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const summaryQuery = useProjectSummary(projectId);
  const latestQuery = useLatestReports(projectId);
  const reportsQuery = useReports(projectId);
  const regenerateMutation = useRegenerateReport(projectId);
  const sendMutation = useSendReport(projectId);
  const { t } = useI18n();

  const summary = summaryQuery.data;
  const latest = latestQuery.data ?? summary?.latest_reports;
  const allReports = reportsQuery.data ?? [];

  const strategicHistory = useMemo(
    () => allReports.filter((item) => item.kind === "strategic"),
    [allReports],
  );
  const periodicHistory = useMemo(
    () => allReports.filter((item) => item.kind === "periodic"),
    [allReports],
  );

  if (summaryQuery.isLoading || latestQuery.isLoading || reportsQuery.isLoading) {
    return <LoadingSpinner />;
  }

  const error =
    (summaryQuery.error instanceof Error && summaryQuery.error.message) ||
    (latestQuery.error instanceof Error && latestQuery.error.message) ||
    (reportsQuery.error instanceof Error && reportsQuery.error.message) ||
    (regenerateMutation.error instanceof Error && regenerateMutation.error.message) ||
    (sendMutation.error instanceof Error && sendMutation.error.message) ||
    "";

  if (!summary) return <ErrorAlert message={t("common.projectNotFound")} />;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <ProjectHeader project={summary.project} />
      <ProjectTabs projectId={projectId} />

      <div className="space-y-6">
        <div className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#ffffff_0%,#f8fafc_45%,#eef2ff_100%)] p-6 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-slate-900 p-2 text-white">
              <FileText className="h-4 w-4" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">AI CMO Reports</h1>
              <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-500">
                Strategic reports explain what the project is, where its moat and risks are, and how
                the market context is shifting. Weekly reports look back across the latest monitored
                data and summarize what changed, why it matters, and what agents should focus on next.
              </p>
              {error ? <div className="mt-4"><ErrorAlert message={error} /></div> : null}
              {sendMutation.data?.ok ? (
                <div className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                  Weekly report emailed to {sendMutation.data.recipient}.
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <ReportSection
          title="Strategic Report"
          description="Generated from project context, current strengths and weaknesses, tracked competitors, and the latest monitoring evidence. This is the board-level view of where the project stands."
          kind="strategic"
          human={latest?.strategic?.human ?? null}
          agent={latest?.strategic?.agent ?? null}
          onRegenerate={(kind) => regenerateMutation.mutate(kind)}
          regenerating={regenerateMutation.isPending && regenerateMutation.variables === "strategic"}
        />

        <ReportSection
          title="Weekly Report"
          description="Generated from the latest seven-day monitoring window. It summarizes the biggest changes, the confidence level of the underlying samples, and the next week’s focus for downstream agents."
          kind="periodic"
          human={latest?.periodic?.human ?? null}
          agent={latest?.periodic?.agent ?? null}
          onRegenerate={(kind) => regenerateMutation.mutate(kind)}
          regenerating={regenerateMutation.isPending && regenerateMutation.variables === "periodic"}
          extraAction={
            <button
              type="button"
              onClick={() => sendMutation.mutate()}
              disabled={sendMutation.isPending}
              className="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Mail className="h-4 w-4" />
              {sendMutation.isPending ? "Sending..." : "Send Weekly Email"}
            </button>
          }
        />

        <div className="grid gap-6 xl:grid-cols-2">
          <ReportHistory title="Strategic History" reports={strategicHistory} />
          <ReportHistory title="Weekly History" reports={periodicHistory} />
        </div>
      </div>
    </div>
  );
}

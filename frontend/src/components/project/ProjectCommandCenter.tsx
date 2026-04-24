import { ArrowRight, Bot, FileText, GitBranch, Globe, PenLine, Search, Users } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";
import type { LatestReports, LatestScans, MonitoringSummary } from "../../types";
import { useI18n } from "../../i18n";
import { useNextActions } from "../../hooks/useProject";
import { utcDate } from "../../utils/time";
import type { TranslationKey } from "../../i18n";
import type { NextAction } from "../../api/projects";

type AgentCardData = {
  key: string;
  title: string;
  icon: React.ElementType;
  found: string;
  why: string;
  next: string;
  action?: ReactNode;
};

function SummaryCard({
  label,
  value,
  body,
}: {
  label: string;
  value: string | number;
  body: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm">
      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
        {label}
      </p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
    </article>
  );
}

function AgentCard({
  title,
  icon: Icon,
  found,
  why,
  next,
  action,
  whatFoundLabel,
  whyLabel,
  nextLabel,
}: AgentCardData & {
  whatFoundLabel: string;
  whyLabel: string;
  nextLabel: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
          <Icon size={18} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-950">{title}</h3>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            {whatFoundLabel}
          </p>
          <p className="mt-1 text-sm leading-6 text-slate-700">{found}</p>
        </div>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            {whyLabel}
          </p>
          <p className="mt-1 text-sm leading-6 text-slate-700">{why}</p>
        </div>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            {nextLabel}
          </p>
          <p className="mt-1 rounded-2xl bg-slate-50 px-3 py-2 text-sm font-medium leading-6 text-slate-950">
            {next}
          </p>
        </div>
        {action && <div className="mt-2">{action}</div>}
      </div>
    </article>
  );
}

function getLatestSerpTimestamp(latest: LatestScans) {
  const timestamps = latest.serp
    .map((snapshot) => snapshot.checked_at)
    .filter((value): value is string => Boolean(value))
    .map((value) => utcDate(value).getTime());

  if (timestamps.length === 0) return null;
  return new Date(Math.max(...timestamps));
}

function countFreshSurfaces(latest: LatestScans) {
  const freshCutoff = Date.now() - 24 * 60 * 60 * 1000;
  const timestamps = [
    latest.seo?.scanned_at ? utcDate(latest.seo.scanned_at).getTime() : null,
    latest.geo?.scanned_at ? utcDate(latest.geo.scanned_at).getTime() : null,
    latest.community?.scanned_at ? utcDate(latest.community.scanned_at).getTime() : null,
    getLatestSerpTimestamp(latest)?.getTime() ?? null,
  ];

  return timestamps.filter((value): value is number => value != null && value >= freshCutoff).length;
}

function hasReadyReport(latestReports?: LatestReports) {
  return Boolean(
    latestReports?.strategic?.human ||
      latestReports?.strategic?.agent ||
      latestReports?.periodic?.human ||
      latestReports?.periodic?.agent,
  );
}

export function ProjectCommandCenter({
  projectId,
  latest,
  latestMonitoring,
  latestReports,
  competitorCount = 0,
  pendingApprovals = 0,
  blogDraftsCount = 0,
  actionsOverride,
  routeOverrides,
  contentAction,
}: {
  projectId: number;
  latest: LatestScans;
  latestMonitoring?: MonitoringSummary | null;
  latestReports?: LatestReports;
  competitorCount?: number;
  pendingApprovals?: number;
  blogDraftsCount?: number;
  actionsOverride?: NextAction[];
  contentAction?: ReactNode;
  routeOverrides?: Partial<Record<
    "changedToday" | "whatMattersNow" | "readyToShip" | "siteHealth" | "aiSearch" | "community" | "competitor" | "report",
    string
  >>;
}) {
  const { data } = useNextActions(projectId, !actionsOverride);
  const { t } = useI18n();
  const actions = actionsOverride ?? data?.actions ?? [];
  const surfaceUpdates = countFreshSurfaces(latest);
  const findingsCount = latestMonitoring?.findings_count ?? 0;
  const recommendationsCount = latestMonitoring?.recommendations_count ?? 0;
  const reportReady = hasReadyReport(latestReports);
  const routes = {
    changedToday: routeOverrides?.changedToday ?? `/projects/${projectId}/seo`,
    whatMattersNow: routeOverrides?.whatMattersNow ?? (pendingApprovals > 0 ? "/approvals" : `/projects/${projectId}/community`),
    readyToShip: routeOverrides?.readyToShip ?? (pendingApprovals > 0 ? "/approvals" : `/projects/${projectId}/reports`),
    siteHealth: routeOverrides?.siteHealth ?? `/projects/${projectId}/seo`,
    aiSearch: routeOverrides?.aiSearch ?? `/projects/${projectId}/geo`,
    community: routeOverrides?.community ?? `/projects/${projectId}/community`,
    competitor: routeOverrides?.competitor ?? `/projects/${projectId}/graph`,
    report: routeOverrides?.report ?? `/projects/${projectId}/reports`,
  };

  const getActionTitle = (domain: string, fallbackKey: TranslationKey) =>
    actions.find((item) => item.domain === domain)?.title ?? t(fallbackKey);
  const routeByDomain = {
    seo: routes.siteHealth,
    geo: routes.aiSearch,
    community: routes.community,
    graph: routes.competitor,
    report: routes.report,
  } satisfies Partial<Record<string, string>>;

  const siteHealthFound =
    latest.seo?.score != null
      ? t("agents.siteHealthFound", { score: Math.round(latest.seo.score * 100) })
      : t("agents.siteHealthPending");
  const aiSearchFound =
    latest.geo?.score != null
      ? t("agents.aiSearchFound", { score: latest.geo.score })
      : t("agents.aiSearchPending");
  const communityFound =
    latest.community?.total_hits != null
      ? t("agents.communityFound", { count: latest.community.total_hits })
      : t("agents.communityPending");
  const competitorFound =
    competitorCount > 0
      ? t("agents.competitorFound", { count: competitorCount })
      : t("agents.competitorPending");
  const reportFound =
    latestMonitoring != null
      ? t("agents.reportFound", { findings: findingsCount, actions: recommendationsCount })
      : t("agents.reportPending");
  const contentFound =
    blogDraftsCount > 0
      ? t("agents.contentFound", { count: blogDraftsCount })
      : t("agents.contentPending");

  const primaryAction =
    pendingApprovals > 0
      ? {
          label: t("command.reviewDraft"),
          to: routes.readyToShip,
          summary: t("project.commandMattersText", { count: findingsCount, approvals: pendingApprovals }),
        }
      : reportReady
        ? {
            label: t("command.exportReport"),
            to: routes.report,
            summary: reportFound,
          }
        : actions[0]
          ? {
              label: t("command.openOpportunities"),
              to: routeByDomain[actions[0].domain as keyof typeof routeByDomain] ?? routes.whatMattersNow,
              summary: actions[0].title,
            }
          : {
              label: t("command.reviewFixes"),
              to: routes.changedToday,
              summary: t("project.commandChangedEmpty"),
            };

  const agentCards: AgentCardData[] = [
    {
      key: "site-health",
      title: t("agents.siteHealth"),
      icon: Search,
      found: siteHealthFound,
      why: t("agents.siteHealthWhy"),
      next: getActionTitle("seo", "agents.defaultNext"),
    },
    {
      key: "ai-search",
      title: t("agents.aiSearch"),
      icon: Globe,
      found: aiSearchFound,
      why: t("agents.aiSearchWhy"),
      next: getActionTitle("geo", "agents.defaultNext"),
    },
    {
      key: "community",
      title: t("agents.community"),
      icon: Users,
      found: communityFound,
      why: t("agents.communityWhy"),
      next: getActionTitle("community", "agents.defaultNext"),
    },
    {
      key: "competitor",
      title: t("agents.competitor"),
      icon: GitBranch,
      found: competitorFound,
      why: t("agents.competitorWhy"),
      next: getActionTitle("graph", "agents.defaultNext"),
    },
    {
      key: "report",
      title: t("agents.report"),
      icon: FileText,
      found: reportFound,
      why: t("agents.reportWhy"),
      next: reportReady ? t("agents.reportNext") : t("agents.defaultNext"),
    },
    {
      key: "content",
      title: t("agents.content"),
      icon: PenLine,
      found: contentFound,
      why: t("agents.contentWhy"),
      next: t("agents.contentNext"),
      action: contentAction,
    },
  ];

  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-slate-200/80 bg-[radial-gradient(circle_at_top,_rgba(99,102,241,0.08),_transparent_40%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-6 shadow-sm">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-white">
              <Bot size={18} />
            </div>
            <div className="max-w-3xl">
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
                {t("project.commandTitle")}
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                {t("project.commandSubtitle")}
              </h2>
            </div>
          </div>

          <div className="max-w-md rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-sm">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
              {t("command.readyToShip")}
            </p>
            <p className="mt-3 text-sm font-semibold leading-6 text-slate-950">
              {primaryAction.summary}
            </p>
            <Link
              to={primaryAction.to}
              className="mt-4 inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-slate-800"
            >
              {primaryAction.label}
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          <SummaryCard
            label={t("command.changedToday")}
            value={surfaceUpdates}
            body={
              surfaceUpdates > 0
                ? t("project.commandChangedText", { count: surfaceUpdates })
                : t("project.commandChangedEmpty")
            }
          />
          <SummaryCard
            label={t("command.whatMattersNow")}
            value={findingsCount}
            body={t("project.commandMattersText", { count: findingsCount, approvals: pendingApprovals })}
          />
          <SummaryCard
            label={t("command.readyToShip")}
            value={recommendationsCount}
            body={
              reportReady
                ? t("project.commandReportReady", { count: recommendationsCount, approvals: pendingApprovals })
                : t("project.commandReportPending", { count: recommendationsCount, approvals: pendingApprovals })
            }
          />
        </div>
      </div>

      <div className="rounded-3xl border border-slate-200/80 bg-white/85 p-5 shadow-sm">
        <div className="mb-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
            {t("agents.title")}
          </p>
          <p className="mt-2 text-sm text-slate-600">{t("agents.subtitle")}</p>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          {agentCards.map(({ key, ...card }) => (
            <AgentCard
              key={key}
              {...card}
              whatFoundLabel={t("agents.whatFound")}
              whyLabel={t("agents.whyMatters")}
              nextLabel={t("agents.nextStep")}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

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
  ExternalLink,
  Sparkles,
} from "lucide-react";
import {
  useTaskArtifacts,
  useTaskPoll,
  useTaskFindings,
  useTaskRecommendations,
  useTaskStale,
} from "../../hooks/useTasks";
import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";
import type {
  AnalysisProgress,
  Finding,
  Recommendation,
  TaskArtifactCluster,
  TaskArtifactOpportunity,
  TaskArtifactQuality,
  TaskArtifactStageCard,
  TaskArtifactWatchout,
} from "../../types";

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
  warning: "bg-amber-50 text-amber-700 ring-amber-200",
};

const SEVERITY_STYLE: Record<string, string> = {
  critical: "bg-rose-50 text-rose-700 ring-rose-200",
  warning: "bg-amber-50 text-amber-700 ring-amber-200",
  info: "bg-slate-50 text-slate-600 ring-slate-200",
};

const PRIORITY_STYLE: Record<string, string> = {
  high: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  medium: "bg-sky-50 text-sky-700 ring-sky-200",
  low: "bg-slate-50 text-slate-600 ring-slate-200",
};

const QUALITY_STYLE: Record<string, string> = {
  reliable: "border-emerald-200 bg-emerald-50/80 text-emerald-900",
  partial: "border-amber-200 bg-amber-50/80 text-amber-900",
  limited: "border-rose-200 bg-rose-50/80 text-rose-900",
};

const QUALITY_BADGE_STYLE: Record<string, string> = {
  reliable: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  partial: "bg-amber-100 text-amber-700 ring-amber-200",
  limited: "bg-rose-100 text-rose-700 ring-rose-200",
};

const STAGE_KIND_STYLE: Record<string, string> = {
  normal: "bg-slate-100 text-slate-600 ring-slate-200",
  fallback: "bg-sky-100 text-sky-700 ring-sky-200",
  degraded: "bg-amber-100 text-amber-700 ring-amber-200",
};

const WATCHOUT_KIND_STYLE: Record<string, string> = {
  source_limit: "bg-amber-100 text-amber-700 ring-amber-200",
  fallback: "bg-sky-100 text-sky-700 ring-sky-200",
  coverage_gap: "bg-rose-100 text-rose-700 ring-rose-200",
  task_error: "bg-rose-100 text-rose-700 ring-rose-200",
};

function getAnalystEvents(progress: AnalysisProgress[]) {
  return progress.filter((item) => item.stage === "domain_review" && item.agent);
}

function legacyIssueToWatchout(issue: { stage: string; status: "warning" | "failed"; summary: string; resolution: string }): TaskArtifactWatchout {
  return {
    stage: issue.stage,
    status: issue.status,
    kind: issue.status === "failed" ? "task_error" : "coverage_gap",
    code: issue.status === "failed" ? "task_error" : "legacy_issue",
    title: issue.summary,
    summary: issue.summary,
    resolution: issue.resolution,
    blocking: issue.status === "failed",
  };
}

function QualityBanner({
  quality,
  t,
}: {
  quality: TaskArtifactQuality;
  t: (key: TranslationKey) => string;
}) {
  return (
    <div className={`rounded-2xl border p-4 ${QUALITY_STYLE[quality.level] ?? QUALITY_STYLE.reliable}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold">{quality.headline}</span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ring-1 ring-inset ${
            QUALITY_BADGE_STYLE[quality.level] ?? QUALITY_BADGE_STYLE.reliable
          }`}
        >
          {quality.level === "reliable" ? t("analysis.qualityReliable") : quality.level === "partial" ? t("analysis.qualityPartial") : t("analysis.qualityLimited")}
        </span>
      </div>
      <p className="mt-2 text-sm leading-relaxed">{quality.summary}</p>
      {quality.fallbacks_used.length > 0 ? (
        <p className="mt-3 text-xs leading-relaxed">
          <span className="font-semibold">{t("analysis.fallbacksUsed")}:</span>{" "}
          {quality.fallbacks_used.join(" · ")}
        </p>
      ) : null}
      {quality.source_warnings.length > 0 ? (
        <p className="mt-2 text-xs leading-relaxed">
          <span className="font-semibold">{t("analysis.sourceWarnings")}:</span>{" "}
          {quality.source_warnings.join(" · ")}
        </p>
      ) : null}
    </div>
  );
}

function WatchoutCard({
  watchout,
  stageLabel,
  t,
}: {
  watchout: TaskArtifactWatchout;
  stageLabel: string;
  t: (key: TranslationKey) => string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">{stageLabel}</span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ring-1 ring-inset ${
            WATCHOUT_KIND_STYLE[watchout.kind] ?? WATCHOUT_KIND_STYLE.coverage_gap
          }`}
        >
          {watchout.kind === "source_limit"
            ? t("analysis.watchoutSourceLimit")
            : watchout.kind === "fallback"
              ? t("analysis.watchoutFallback")
              : watchout.kind === "coverage_gap"
                ? t("analysis.watchoutCoverageGap")
                : t("analysis.watchoutTaskError")}
        </span>
        {watchout.blocking ? (
          <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-rose-700 ring-1 ring-inset ring-rose-200">
            {t("analysis.blocking")}
          </span>
        ) : null}
      </div>
      <p className="text-sm font-semibold text-slate-900">{watchout.title}</p>
      <p className="mt-1 text-sm leading-relaxed text-slate-600">{watchout.summary}</p>
      <p className="mt-2 text-sm leading-relaxed text-slate-700">{watchout.resolution}</p>
    </div>
  );
}

function EvidenceRefs({
  refs,
  label,
}: {
  refs: Finding["evidence_refs"];
  label: string;
}) {
  if (!refs?.length) return null;

  return (
    <div className="mt-3">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
        {label}
      </p>
      <div className="flex flex-wrap gap-2">
        {refs.slice(0, 4).map((ref, index) => {
          const content = (
            <>
              <span className="font-medium text-slate-500">{ref.source}</span>
              <span className="text-slate-400">·</span>
              <span className="text-slate-700">{ref.key}</span>
              <span className="text-slate-400">=</span>
              <span className="font-medium text-slate-900">{ref.value}</span>
            </>
          );

          if (ref.url) {
            return (
              <a
                key={`${ref.source}-${ref.key}-${index}`}
                href={ref.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1.5 text-xs ring-1 ring-inset ring-slate-200 transition-colors hover:bg-slate-50"
              >
                {content}
                <ExternalLink size={12} className="text-slate-400" />
              </a>
            );
          }

          return (
            <div
              key={`${ref.source}-${ref.key}-${index}`}
              className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1.5 text-xs ring-1 ring-inset ring-slate-200"
            >
              {content}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function FindingCard({
  finding,
  evidenceLabel,
}: {
  finding: Finding;
  evidenceLabel: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {finding.domain}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ring-1 ring-inset ${
            SEVERITY_STYLE[finding.severity] ?? SEVERITY_STYLE.info
          }`}
        >
          {finding.severity}
        </span>
      </div>
      <p className="text-sm font-semibold text-slate-900">{finding.title}</p>
      <p className="mt-1 text-sm leading-relaxed text-slate-600">{finding.summary}</p>
      <EvidenceRefs refs={finding.evidence_refs} label={evidenceLabel} />
    </div>
  );
}

function RecommendationCard({
  recommendation,
  evidenceLabel,
  rationaleLabel,
}: {
  recommendation: Recommendation;
  evidenceLabel: string;
  rationaleLabel: string;
}) {
  return (
    <div className="rounded-2xl border border-indigo-100 bg-indigo-50/60 p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-indigo-500">
          {recommendation.owner_type}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ring-1 ring-inset ${
            PRIORITY_STYLE[recommendation.priority] ?? PRIORITY_STYLE.low
          }`}
        >
          {recommendation.priority}
        </span>
      </div>
      <p className="text-sm font-semibold text-slate-900">{recommendation.title}</p>
      <p className="mt-1 text-sm leading-relaxed text-slate-600">{recommendation.summary}</p>
      {recommendation.rationale ? (
        <p className="mt-3 text-xs leading-relaxed text-indigo-900/80">
          <span className="font-semibold">{rationaleLabel}: </span>
          {recommendation.rationale}
        </p>
      ) : null}
      <EvidenceRefs refs={recommendation.evidence_refs} label={evidenceLabel} />
    </div>
  );
}

function OpportunityCard({
  opportunity,
  evidenceLabel,
  actionLabel,
}: {
  opportunity: TaskArtifactOpportunity;
  evidenceLabel: string;
  actionLabel: string;
}) {
  return (
    <div className="rounded-2xl border border-sky-100 bg-sky-50/70 p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-sky-600">
          {opportunity.type.replaceAll("_", " ")}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ring-1 ring-inset ${
            PRIORITY_STYLE[opportunity.priority] ?? PRIORITY_STYLE.low
          }`}
        >
          {opportunity.priority}
        </span>
        <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold uppercase text-slate-500 ring-1 ring-inset ring-slate-200">
          {opportunity.score}
        </span>
      </div>
      <p className="text-sm font-semibold text-slate-900">{opportunity.title}</p>
      <p className="mt-1 text-sm leading-relaxed text-slate-600">{opportunity.summary}</p>
      <p className="mt-3 text-xs leading-relaxed text-sky-900/80">
        <span className="font-semibold">{actionLabel}: </span>
        {opportunity.recommended_action}
      </p>
      <EvidenceRefs refs={opportunity.evidence_refs} label={evidenceLabel} />
    </div>
  );
}

function ClusterCard({
  cluster,
  gapsLabel,
  quickWinsLabel,
}: {
  cluster: TaskArtifactCluster;
  gapsLabel: string;
  quickWinsLabel: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-slate-900">{cluster.name}</span>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-slate-600">
          {cluster.opportunity_score}
        </span>
      </div>
      <p className="text-xs text-slate-500">
        {cluster.brand_keyword_count} brand · {cluster.competitor_keyword_count} competitor
      </p>
      {cluster.gap_keywords.length ? (
        <div className="mt-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            {gapsLabel}
          </p>
          <div className="flex flex-wrap gap-2">
            {cluster.gap_keywords.map((keyword) => (
              <span
                key={`${cluster.name}-${keyword}`}
                className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-200"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      ) : null}
      {cluster.quick_win_keywords.length ? (
        <div className="mt-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            {quickWinsLabel}
          </p>
          <div className="flex flex-wrap gap-2">
            {cluster.quick_win_keywords.map((keyword) => (
              <span
                key={`${cluster.name}-qw-${keyword}`}
                className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function SummaryMetric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-2xl bg-white/80 p-4 ring-1 ring-inset ring-white/70">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{value}</p>
    </div>
  );
}

function StageCard({
  card,
  label,
  t,
}: {
  card: TaskArtifactStageCard;
  label: string;
  t: (key: TranslationKey) => string;
}) {
  const cfg = STAGE_CONFIG[card.stage] ?? STAGE_CONFIG.context_build!;
  const Icon = cfg.icon;
  const style = STATUS_STYLE[card.status] ?? STATUS_STYLE.started;

  return (
    <div className={`rounded-xl p-4 ring-1 ring-inset ${style}`}>
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Icon size={14} />
          <span className="text-xs font-semibold">{label}</span>
          {card.kind && card.kind !== "normal" ? (
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ring-1 ring-inset ${
                STAGE_KIND_STYLE[card.kind] ?? STAGE_KIND_STYLE.normal
              }`}
            >
              {card.kind === "fallback" ? t("analysis.stageFallback") : t("analysis.stageDegraded")}
            </span>
          ) : null}
        </div>
        <span className="text-[10px] font-semibold uppercase tracking-wider opacity-80">
          {card.status}
        </span>
      </div>
      <p className="text-sm leading-relaxed">{card.summary}</p>
      {card.hint ? (
        <p className="mt-3 text-xs leading-relaxed opacity-90">{card.hint}</p>
      ) : null}
    </div>
  );
}

function buildLiveStageCards(
  progress: AnalysisProgress[],
  stageCards: TaskArtifactStageCard[],
): TaskArtifactStageCard[] {
  const stageMap = new Map(stageCards.map((card) => [card.stage, card]));

  for (const item of progress) {
    const stage = item.stage;
    if (!stage || !STAGE_CONFIG[stage]) continue;
    const current = stageMap.get(stage);
    stageMap.set(stage, {
      stage,
      status: item.status ?? current?.status ?? "running",
      summary: item.summary ?? item.detail ?? item.content ?? current?.summary ?? "",
      agent: item.agent ?? current?.agent ?? "",
      event_count: (current?.event_count ?? 0) + 1,
      kind: current?.kind,
      hint: current?.hint,
    });
  }

  return Object.keys(STAGE_CONFIG).map((stage) => {
    const card = stageMap.get(stage);
    if (card) return card;
    return {
      stage,
      status: "started",
      summary: "",
      agent: "",
      event_count: 0,
    };
  });
}

function cleanProgressText(value: string | undefined) {
  return (value ?? "").trim();
}

function uniqueSummaries(values: string[], limit = 3) {
  const seen = new Set<string>();
  const unique: string[] = [];

  for (const value of values) {
    const normalized = cleanProgressText(value);
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    unique.push(normalized);
  }

  return unique.slice(0, limit);
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
  const isDone = task?.status === "completed" || task?.status === "failed";
  const { data: artifacts } = useTaskArtifacts(taskId, !!taskId, !isDone);
  const { t } = useI18n();

  const progress: AnalysisProgress[] = task?.progress ?? [];
  const isStale = useTaskStale(task?.status, progress.length);
  const analystEvents = useMemo(() => getAnalystEvents(progress), [progress]);
  const stageCards = artifacts?.stage_cards ?? [];
  const liveStageCards = useMemo(() => buildLiveStageCards(progress, stageCards), [progress, stageCards]);
  const watchouts = useMemo(
    () => (artifacts?.watchouts?.length ? artifacts.watchouts : (artifacts?.issues ?? []).map(legacyIssueToWatchout)),
    [artifacts?.issues, artifacts?.watchouts],
  );
  const quality = artifacts?.quality;
  const topOpportunities = artifacts?.opportunities?.top ?? [];
  const topClusters = artifacts?.cluster_summary?.top_clusters ?? [];
  const displayedStageCards = isDone && stageCards.length > 0 ? stageCards : liveStageCards;
  const completedStageCount = liveStageCards.filter((card) => card.status === "completed" || card.status === "warning").length;
  const progressPercent = isDone ? 100 : Math.round((completedStageCount / Math.max(liveStageCards.length, 1)) * 100);
  const currentStageCard = liveStageCards.find((card) => card.status === "running") ?? liveStageCards[completedStageCount];
  const latestProgressEntry = [...progress].reverse().find((item) => item.summary || item.detail || item.content);
  const latestProgressSummary = latestProgressEntry?.summary ?? latestProgressEntry?.detail ?? latestProgressEntry?.content ?? task?.summary ?? "";
  const contextSnapshot = [...progress]
    .reverse()
    .find((item) => item.stage === "context_build" && cleanProgressText(item.summary ?? item.detail ?? item.content));
  const signalHighlights = uniqueSummaries(
    progress
      .filter((item) => item.stage === "signal_collect" && item.status !== "started")
      .map((item) => item.summary ?? item.detail ?? item.content)
      .filter((item): item is string => Boolean(item)),
    4,
  );
  const domainHighlights = uniqueSummaries(
    progress
      .filter((item) => item.stage === "domain_review" && item.agent)
      .map((item) => item.detail ?? item.summary ?? item.content)
      .filter((item): item is string => Boolean(item)),
    4,
  );
  const strategyDraft = [...progress]
    .reverse()
    .find((item) => item.stage === "strategy_synthesis" && cleanProgressText(item.summary ?? item.detail ?? item.content));
  const livePreviewCards = [
    {
      key: "context",
      title: t("analysis.contextSnapshot"),
      body: cleanProgressText(contextSnapshot?.summary ?? contextSnapshot?.detail ?? contextSnapshot?.content) || t("analysis.focusPending"),
      items: [] as string[],
    },
    {
      key: "signals",
      title: t("analysis.signalHighlights"),
      body:
        topOpportunities[0]?.summary ??
        signalHighlights[0] ??
        t("analysis.focusPending"),
      items:
        topOpportunities.length > 0
          ? topOpportunities.slice(0, 3).map((item) => item.title)
          : signalHighlights,
    },
    {
      key: "review",
      title: t("analysis.reviewNotes"),
      body: domainHighlights[0] ?? t("analysis.focusPending"),
      items: domainHighlights,
    },
    {
      key: "draft",
      title: t("analysis.draftActions"),
      body:
        cleanProgressText(strategyDraft?.summary ?? strategyDraft?.detail ?? strategyDraft?.content) ||
        topOpportunities[0]?.recommended_action ||
        t("analysis.focusPending"),
      items:
        topClusters.length > 0
          ? topClusters.slice(0, 3).map((cluster) => cluster.name)
          : [],
    },
  ].filter((card) => card.body !== t("analysis.focusPending") || card.items.length > 0);

  const { data: findings = [] } = useTaskFindings(taskId, isDone);
  const { data: recommendations = [] } = useTaskRecommendations(taskId, isDone);
  const blockingWatchout = watchouts.find((item) => item.blocking);

  useEffect(() => {
    const el = document.getElementById("analysis-scroll");
    if (el) el.scrollTop = el.scrollHeight;
  }, [progress.length, findings.length, recommendations.length, watchouts.length, topOpportunities.length, topClusters.length]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="flex h-[82vh] w-full max-w-4xl flex-col rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{t("analysis.title")}</h2>
            <p className="mt-0.5 max-w-xl truncate text-xs text-slate-400">{url}</p>
            <p className="mt-0.5 text-xs text-slate-400">{t("analysis.backgroundHint")}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        <div id="analysis-scroll" className="flex-1 space-y-6 overflow-y-auto px-6 py-4">
          {!isDone && !isStale && (
            <section className="overflow-hidden rounded-3xl border border-slate-200/80 bg-[radial-gradient(circle_at_top,_rgba(99,102,241,0.12),_transparent_42%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-6 shadow-sm">
              <div className="grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-indigo-500">
                    {t("analysis.progressTitle")}
                  </p>
                  <h3 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
                    {t("analysis.progressSubtitle")}
                  </h3>
                  <div className="mt-4 flex items-center gap-3">
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-indigo-500 transition-all duration-700"
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-slate-600">{progressPercent}%</span>
                  </div>

                  <div className="mt-4 rounded-2xl border border-slate-200/80 bg-white/80 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                      {t("analysis.currentFocus")}
                    </p>
                    <p className="mt-2 text-sm font-semibold text-slate-950">
                      {currentStageCard ? t(STAGE_CONFIG[currentStageCard.stage]?.labelKey ?? "analysis.stageContextBuild") : t("analysis.initializing")}
                    </p>
                    <p className="mt-2 text-sm leading-6 text-slate-600">
                      {latestProgressSummary || t("analysis.focusPending")}
                    </p>
                    {currentStageCard?.hint ? (
                      <p className="mt-3 text-xs leading-5 text-slate-500">{currentStageCard.hint}</p>
                    ) : null}
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                  {[
                    { title: t("welcome.featureSeo"), desc: t("welcome.featureSeoDesc") },
                    { title: t("welcome.featureGeo"), desc: t("welcome.featureGeoDesc") },
                    { title: t("welcome.featureCommunity"), desc: t("welcome.featureCommunityDesc") },
                  ].map((item) => (
                    <div key={item.title} className="rounded-2xl border border-slate-200/80 bg-white/80 p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                        {t("analysis.livePreview")}
                      </p>
                      <p className="mt-2 text-sm font-semibold text-slate-950">{item.title}</p>
                      <p className="mt-2 text-sm leading-6 text-slate-600">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {quality && quality.level !== "reliable" ? (
                <div className="mt-5">
                  <QualityBanner quality={quality} t={t} />
                </div>
              ) : null}
            </section>
          )}

          {!isDone && livePreviewCards.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <Sparkles size={14} className="text-indigo-500" />
                <h3 className="text-sm font-semibold text-slate-900">{t("analysis.resultsArriving")}</h3>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {livePreviewCards.map((card) => (
                  <div
                    key={card.key}
                    className="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm"
                  >
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                      {card.title}
                    </p>
                    <p className="mt-2 text-sm font-medium leading-6 text-slate-950">{card.body}</p>
                    {card.items.length > 1 ? (
                      <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
                        {card.items.slice(0, 3).map((item) => (
                          <li key={item} className="flex gap-2">
                            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-300" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ))}
              </div>
            </section>
          )}

          {isStale && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <TriangleAlert size={32} className="mb-3 text-amber-500" />
              <p className="text-sm font-medium text-amber-600">{t("analysis.taskStale")}</p>
            </div>
          )}

          {isDone && artifacts?.overview ? (
            <section className="overflow-hidden rounded-3xl border border-slate-200/80 bg-[radial-gradient(circle_at_top_right,_rgba(99,102,241,0.16),_transparent_38%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-6 shadow-sm">
              <div className="flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600 ring-1 ring-indigo-200/70">
                  <Sparkles size={18} />
                </div>
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-indigo-500">
                    {t("analysis.summaryTitle")}
                  </p>
                  <h3 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
                    {artifacts.overview.headline}
                  </h3>
                  <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
                    {t("analysis.summarySubtitle")}
                  </p>
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <SummaryMetric
                  label={t("analysis.keyFindings")}
                  value={artifacts.overview.findings_count}
                />
                <SummaryMetric
                  label={t("analysis.recommendedActions")}
                  value={artifacts.overview.recommendations_count}
                />
                <SummaryMetric
                  label={t("analysis.dataQuality")}
                  value={
                    quality?.level === "reliable"
                      ? t("analysis.qualityReliable")
                      : quality?.level === "partial"
                        ? t("analysis.qualityPartial")
                        : quality?.level === "limited"
                          ? t("analysis.qualityLimited")
                          : "—"
                  }
                />
              </div>

              {quality ? (
                <div className="mt-5">
                  <QualityBanner quality={quality} t={t} />
                </div>
              ) : null}

              <div className="mt-5 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-2xl bg-white/80 p-4 ring-1 ring-inset ring-slate-200/70">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                    {t("analysis.focusAreas")}
                  </p>
                  {artifacts.overview.focus_domains.length ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {artifacts.overview.focus_domains.map((domain) => (
                        <span
                          key={domain}
                          className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700"
                        >
                          {domain}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-slate-500">{t("analysis.focusPending")}</p>
                  )}
                </div>

                {blockingWatchout ? (
                  <div className="rounded-2xl bg-rose-950 p-4 text-white shadow-sm">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-rose-200">
                      {t("analysis.nextBestAction")}
                    </p>
                    <p className="mt-3 text-sm font-semibold leading-relaxed">
                      {blockingWatchout.title}
                    </p>
                    <p className="mt-2 text-sm leading-relaxed text-rose-100/90">
                      {blockingWatchout.resolution}
                    </p>
                  </div>
                ) : artifacts.brief.top_recommendations[0] ? (
                  <div className="rounded-2xl bg-indigo-950 p-4 text-white shadow-sm">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-indigo-200">
                      {t("analysis.nextBestAction")}
                    </p>
                    <p className="mt-3 text-sm font-semibold leading-relaxed">
                      {artifacts.brief.top_recommendations[0].title}
                    </p>
                    <p className="mt-2 text-sm leading-relaxed text-indigo-100/90">
                      {artifacts.brief.top_recommendations[0].summary}
                    </p>
                  </div>
                ) : topOpportunities[0] ? (
                  <div className="rounded-2xl bg-sky-950 p-4 text-white shadow-sm">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-200">
                      {t("analysis.nextBestAction")}
                    </p>
                    <p className="mt-3 text-sm font-semibold leading-relaxed">
                      {topOpportunities[0].title}
                    </p>
                    <p className="mt-2 text-sm leading-relaxed text-sky-100/90">
                      {topOpportunities[0].summary}
                    </p>
                  </div>
                ) : null}
              </div>
            </section>
          ) : null}

          {isDone && topOpportunities.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <Sparkles size={14} className="text-sky-500" />
                <h3 className="text-sm font-semibold text-slate-900">
                  {t("analysis.opportunities")}
                </h3>
              </div>
              <div className="space-y-3">
                {topOpportunities.map((opportunity, index) => (
                  <OpportunityCard
                    key={`${opportunity.type}-${opportunity.title}-${index}`}
                    opportunity={opportunity}
                    evidenceLabel={t("analysis.evidence")}
                    actionLabel={t("analysis.recommendedMove")}
                  />
                ))}
              </div>
            </section>
          )}

          {isDone && topClusters.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <Target size={14} className="text-slate-500" />
                <h3 className="text-sm font-semibold text-slate-900">
                  {t("analysis.clusterGaps")}
                </h3>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {topClusters.map((cluster) => (
                  <ClusterCard
                    key={cluster.name}
                    cluster={cluster}
                    gapsLabel={t("analysis.gapKeywords")}
                    quickWinsLabel={t("analysis.quickWinKeywords")}
                  />
                ))}
              </div>
            </section>
          )}

          {watchouts.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <TriangleAlert size={14} className="text-amber-500" />
                <h3 className="text-sm font-semibold text-slate-900">{t("analysis.coverageWatchouts")}</h3>
              </div>
              <div className="space-y-3">
                {watchouts.map((watchout, index) => {
                  const labelKey = STAGE_CONFIG[watchout.stage]?.labelKey;
                  return (
                    <WatchoutCard
                      key={`${watchout.stage}-${watchout.code}-${index}`}
                      watchout={watchout}
                      stageLabel={labelKey ? t(labelKey) : watchout.stage}
                      t={t}
                    />
                  );
                })}
              </div>
            </section>
          )}

          {displayedStageCards.length > 0 && (
            <section>
              <div className="mb-3 flex items-center gap-2">
                <div className="h-px flex-1 bg-slate-100" />
                <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                  {t("analysis.workflowStages")}
                </span>
                <div className="h-px flex-1 bg-slate-100" />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {displayedStageCards.map((card) => {
                  const labelKey = STAGE_CONFIG[card.stage]?.labelKey;
                  return (
                    <StageCard
                      key={card.stage}
                      card={card}
                      label={labelKey ? t(labelKey) : card.stage}
                      t={t}
                    />
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
                  <div
                    key={`${item.agent}-${index}`}
                    className="rounded-xl bg-slate-50 p-4 ring-1 ring-inset ring-slate-200"
                  >
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
                <h3 className="text-sm font-semibold text-slate-900">{t("analysis.keyFindings")}</h3>
              </div>
              {quality && quality.level !== "reliable" ? (
                <p className="mb-3 text-sm leading-relaxed text-slate-600">
                  {t("analysis.resultConfidenceNote")}
                </p>
              ) : null}
              <div className="space-y-3">
                {findings.map((finding, index) => (
                  <FindingCard
                    key={`${finding.domain}-${finding.title}-${index}`}
                    finding={finding}
                    evidenceLabel={t("analysis.evidence")}
                  />
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
              {quality && quality.level !== "reliable" ? (
                <p className="mb-3 text-sm leading-relaxed text-slate-600">
                  {t("analysis.resultConfidenceNote")}
                </p>
              ) : null}
              <div className="space-y-3">
                {recommendations.map((recommendation, index) => (
                  <RecommendationCard
                    key={`${recommendation.domain}-${recommendation.title}-${index}`}
                    recommendation={recommendation}
                    evidenceLabel={t("analysis.evidence")}
                    rationaleLabel={t("analysis.rationale")}
                  />
                ))}
              </div>
            </section>
          )}

          {isDone && findings.length === 0 && recommendations.length === 0 && (
            <p className="py-8 text-center text-sm text-slate-400">{t("analysis.noRecordedFindings")}</p>
          )}

          {task?.summary && !isDone && (
            <div className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-700 ring-1 ring-inset ring-slate-200">
              {task.summary}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 px-6 py-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            {isDone ? (
              <>
                <CheckCircle
                  size={14}
                  className={task?.status === "failed" ? "text-rose-500" : "text-emerald-500"}
                />
                <span className={task?.status === "failed" ? "text-rose-600" : "text-emerald-600"}>
                  {task?.status === "failed" ? t("analysis.workflowFailed") : t("analysis.workflowComplete")}
                </span>
              </>
            ) : isStale ? (
              <>
                <TriangleAlert size={14} className="text-amber-500" />
                <span className="text-amber-600">{t("analysis.taskStale")}</span>
              </>
            ) : (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>
                  {stageCards.length}
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

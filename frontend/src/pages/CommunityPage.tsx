import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { useDiscussions, useCommunityChart } from "../hooks/useCommunityData";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { EmptyState } from "../components/common/EmptyState";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { KpiCard } from "../components/common/KpiCard";
import { ChartCard } from "../components/common/ChartCard";
import { CommunityBarChart } from "../components/charts/CommunityBarChart";
import { PlatformBreakdownChart } from "../components/charts/PlatformBreakdownChart";
import { ExternalLink, Users, MessageCircle, Flame, Layers } from "lucide-react";
import { useI18n } from "../i18n";

const PLATFORM_BADGE: Record<string, string> = {
  reddit: "bg-orange-100 text-orange-700",
  hackernews: "bg-orange-50 text-orange-600",
  twitter: "bg-sky-100 text-sky-700",
  stackoverflow: "bg-yellow-100 text-yellow-700",
  github: "bg-indigo-100 text-indigo-700",
};

export function CommunityPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: summary, isLoading } = useProjectSummary(projectId);
  const { data: discussions } = useDiscussions(projectId);
  const { data: chart } = useCommunityChart(projectId);
  const { t } = useI18n();

  if (isLoading) return <LoadingSpinner />;
  if (!summary) return <ErrorAlert message={t("common.projectNotFound")} />;

  const latestHits = chart?.scan_hits?.[chart.scan_hits.length - 1] ?? 0;
  const prevHits = chart?.scan_hits?.[chart.scan_hits.length - 2];
  const hitsDelta =
    prevHits != null && prevHits > 0
      ? ((latestHits - prevHits) / prevHits) * 100
      : null;

  const avgEngagement =
    discussions?.length
      ? discussions.reduce((s, d) => s + (d.engagement_score ?? 0), 0) / discussions.length
      : null;

  const platformCount = discussions?.length
    ? new Set(discussions.map((d) => d.platform)).size
    : 0;

  const maxEngagement = discussions?.length
    ? Math.max(...discussions.map((d) => d.engagement_score ?? 0), 1)
    : 1;

  // Sort discussions by engagement_score descending
  const sorted = [...(discussions ?? [])].sort(
    (a, b) => (b.engagement_score ?? 0) - (a.engagement_score ?? 0),
  );

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <ProjectHeader project={summary.project} />
      <ProjectTabs projectId={projectId} />
      <div className="space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <KpiCard
            icon={Users}
            label={t("community.trackedDiscussions")}
            value={discussions?.length ?? 0}
            accentBg="bg-amber-50"
            accentText="text-amber-600"
          />
          <KpiCard
            icon={MessageCircle}
            label="Latest Hits"
            value={latestHits}
            delta={hitsDelta}
            accentBg="bg-amber-50"
            accentText="text-amber-600"
          />
          <KpiCard
            icon={Flame}
            label="Avg Engagement"
            value={avgEngagement != null ? avgEngagement.toFixed(1) : null}
            accentBg="bg-amber-50"
            accentText="text-amber-600"
          />
          <KpiCard
            icon={Layers}
            label="Platforms"
            value={platformCount}
            accentBg="bg-amber-50"
            accentText="text-amber-600"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {chart?.scan_labels?.length ? (
            <ChartCard title={t("community.scanHistory")} accentBorder="border-l-amber-500">
              <CommunityBarChart data={chart} />
            </ChartCard>
          ) : null}
          {chart?.platform_labels?.length ? (
            <ChartCard title="Platform Breakdown" accentBorder="border-l-amber-500">
              <PlatformBreakdownChart
                labels={chart.platform_labels}
                counts={chart.platform_counts}
              />
            </ChartCard>
          ) : null}
        </div>

        {/* Enhanced Discussion List */}
        <ChartCard
          title={t("community.trackedDiscussions")}
          subtitle={discussions?.length ? `${discussions.length} discussions` : undefined}
          accentBorder="border-l-amber-500"
        >
          {!sorted.length ? (
            <EmptyState
              title={t("community.noDiscussions")}
              description={t("community.noDiscussionsDesc")}
            />
          ) : (
            <div className="space-y-0.5">
              {sorted.map((d) => {
                const badgeClass =
                  PLATFORM_BADGE[d.platform.toLowerCase()] ?? "bg-zinc-100 text-zinc-600";
                const engRatio = (d.engagement_score ?? 0) / maxEngagement;
                const barColor =
                  engRatio > 0.7
                    ? "bg-emerald-500"
                    : engRatio > 0.4
                      ? "bg-amber-400"
                      : "bg-zinc-300";
                return (
                  <div
                    key={d.id}
                    className="flex items-center gap-3 rounded-lg border-b border-zinc-50 px-3 py-3 transition-colors hover:bg-zinc-50"
                  >
                    {/* Platform Badge */}
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${badgeClass}`}
                    >
                      {d.platform}
                    </span>

                    {/* Title + link */}
                    <div className="min-w-0 flex-1">
                      <a
                        href={d.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-sm font-medium text-blue-600 hover:underline"
                      >
                        <span className="truncate">{d.title}</span>
                        <ExternalLink size={12} className="shrink-0" />
                      </a>
                    </div>

                    {/* Engagement mini-bar */}
                    <div className="flex w-24 items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-100">
                        <div
                          className={`h-full rounded-full ${barColor} transition-all duration-500`}
                          style={{ width: `${engRatio * 100}%` }}
                        />
                      </div>
                      <span className="w-8 text-right font-mono text-xs text-zinc-500">
                        {d.engagement_score ?? 0}
                      </span>
                    </div>

                    {/* Comment count */}
                    <div className="flex items-center gap-1 text-xs text-zinc-400">
                      <MessageCircle size={12} />
                      {d.comments_count ?? 0}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </ChartCard>
      </div>
    </div>
  );
}

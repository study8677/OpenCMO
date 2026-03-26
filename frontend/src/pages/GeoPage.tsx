import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { useGeoChart } from "../hooks/useGeoData";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { EmptyState } from "../components/common/EmptyState";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { KpiCard } from "../components/common/KpiCard";
import { ChartCard } from "../components/common/ChartCard";
import { GeoScoreChart } from "../components/charts/GeoScoreChart";
import { useI18n } from "../i18n";
import { Globe, Eye, MapPin, Heart } from "lucide-react";

function getDelta(arr: (number | null)[] | undefined): number | null {
  if (!arr || arr.length < 2) return null;
  const curr = arr[arr.length - 1];
  const prev = arr[arr.length - 2];
  if (curr == null || prev == null || prev === 0) return null;
  return ((curr - prev) / Math.abs(prev)) * 100;
}

function latest(arr: (number | null)[] | undefined): number | null {
  if (!arr || !arr.length) return null;
  return arr[arr.length - 1] ?? null;
}

const SNAPSHOT_SERIES = [
  { key: "geo_score", label: "GEO Score", color: "bg-emerald-500" },
  { key: "visibility", label: "Visibility", color: "bg-violet-500" },
  { key: "position", label: "Position", color: "bg-sky-500" },
  { key: "sentiment", label: "Sentiment", color: "bg-amber-500" },
];

export function GeoPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: summary, isLoading: loadingSummary } = useProjectSummary(projectId);
  const { data: chart, isLoading: loadingChart } = useGeoChart(projectId);
  const { t } = useI18n();

  if (loadingSummary) return <LoadingSpinner />;
  if (!summary) return <ErrorAlert message={t("common.projectNotFound")} />;

  const geoScore = chart?.geo_score as (number | null)[] | undefined;
  const visibility = chart?.visibility as (number | null)[] | undefined;
  const position = chart?.position as (number | null)[] | undefined;
  const sentiment = chart?.sentiment as (number | null)[] | undefined;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <ProjectHeader project={summary.project} />
      <ProjectTabs projectId={projectId} />
      {loadingChart ? (
        <LoadingSpinner />
      ) : !chart?.labels?.length ? (
        <EmptyState title={t("geo.noData")} description={t("geo.noDataDesc")} />
      ) : (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <KpiCard
              icon={Globe}
              label="GEO Score"
              value={latest(geoScore) != null ? `${Math.round(latest(geoScore)!)}/100` : null}
              delta={getDelta(geoScore)}
              accentBg="bg-emerald-50"
              accentText="text-emerald-600"
            />
            <KpiCard
              icon={Eye}
              label="Visibility"
              value={latest(visibility) != null ? `${Math.round(latest(visibility)!)}/100` : null}
              delta={getDelta(visibility)}
              accentBg="bg-emerald-50"
              accentText="text-emerald-600"
            />
            <KpiCard
              icon={MapPin}
              label="Position"
              value={latest(position) != null ? `${Math.round(latest(position)!)}/100` : null}
              delta={getDelta(position)}
              accentBg="bg-emerald-50"
              accentText="text-emerald-600"
            />
            <KpiCard
              icon={Heart}
              label="Sentiment"
              value={latest(sentiment) != null ? `${Math.round(latest(sentiment)!)}/100` : null}
              delta={getDelta(sentiment)}
              accentBg="bg-emerald-50"
              accentText="text-emerald-600"
            />
          </div>

          {/* AI Visibility Trends */}
          <ChartCard title={t("geo.scoreTrend")} accentBorder="border-l-emerald-500">
            <GeoScoreChart data={chart} />
          </ChartCard>

          {/* Latest Snapshot — progress bars */}
          <ChartCard title="Latest Snapshot" accentBorder="border-l-emerald-500">
            <div className="space-y-4">
              {SNAPSHOT_SERIES.map((s) => {
                const arr = chart[s.key] as (number | null)[] | undefined;
                const val = arr?.[arr.length - 1];
                return (
                  <div key={s.key}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium text-zinc-700">{s.label}</span>
                      <span className="font-mono text-zinc-500">
                        {val != null ? Math.round(val) : "—"}/100
                      </span>
                    </div>
                    <div className="h-3 w-full overflow-hidden rounded-full bg-zinc-100">
                      <div
                        className={`h-full rounded-full ${s.color} transition-all duration-700`}
                        style={{ width: `${val != null ? Math.min(val, 100) : 0}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </ChartCard>
        </div>
      )}
    </div>
  );
}

import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { useSeoChart } from "../hooks/useSeoData";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { EmptyState } from "../components/common/EmptyState";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { KpiCard } from "../components/common/KpiCard";
import { ChartCard } from "../components/common/ChartCard";
import { SeoPerformanceChart } from "../components/charts/SeoPerformanceChart";
import { CwvMiniChart } from "../components/charts/CwvMiniChart";
import { useI18n } from "../i18n";
import { Gauge, Timer, Move, Zap } from "lucide-react";

function getCwvStatus(value: number | null | undefined, good: number, poor: number): "good" | "warning" | "poor" {
  if (value == null) return "warning";
  return value <= good ? "good" : value <= poor ? "warning" : "poor";
}

function getDelta(arr: (number | null)[] | undefined): number | null {
  if (!arr || arr.length < 2) return null;
  const curr = arr[arr.length - 1];
  const prev = arr[arr.length - 2];
  if (curr == null || prev == null || prev === 0) return null;
  return ((curr - prev) / Math.abs(prev)) * 100;
}

export function SeoPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: summary, isLoading: loadingSummary } = useProjectSummary(projectId);
  const { data: chart, isLoading: loadingChart } = useSeoChart(projectId);
  const { t } = useI18n();

  if (loadingSummary) return <LoadingSpinner />;
  if (!summary) return <ErrorAlert message={t("common.projectNotFound")} />;

  const perf = chart?.performance as (number | null)[] | undefined;
  const lcp = chart?.lcp as (number | null)[] | undefined;
  const cls = chart?.cls as (number | null)[] | undefined;
  const tbt = chart?.tbt as (number | null)[] | undefined;

  const latestPerf = perf?.[perf.length - 1];
  const latestLcp = lcp?.[lcp.length - 1];
  const latestCls = cls?.[cls.length - 1];
  const latestTbt = tbt?.[tbt.length - 1];

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <ProjectHeader project={summary.project} />
      <ProjectTabs projectId={projectId} />
      {loadingChart ? (
        <LoadingSpinner />
      ) : !chart?.labels?.length ? (
        <EmptyState title={t("seo.noData")} description={t("seo.noDataDesc")} />
      ) : (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <KpiCard
              icon={Gauge}
              label={t("seo.performanceScore")}
              value={latestPerf != null ? `${Math.round(latestPerf * 100)}%` : null}
              delta={getDelta(perf)}
              status={latestPerf != null ? (latestPerf >= 0.9 ? "good" : latestPerf >= 0.5 ? "warning" : "poor") : undefined}
              accentBg="bg-sky-50"
              accentText="text-sky-600"
            />
            <KpiCard
              icon={Timer}
              label="LCP"
              value={latestLcp != null ? `${latestLcp.toFixed(1)}s` : null}
              delta={getDelta(lcp)}
              status={getCwvStatus(latestLcp, 2.5, 4)}
              accentBg="bg-sky-50"
              accentText="text-sky-600"
            />
            <KpiCard
              icon={Move}
              label="CLS"
              value={latestCls != null ? latestCls.toFixed(3) : null}
              delta={getDelta(cls)}
              status={getCwvStatus(latestCls, 0.1, 0.25)}
              accentBg="bg-sky-50"
              accentText="text-sky-600"
            />
            <KpiCard
              icon={Zap}
              label="TBT"
              value={latestTbt != null ? `${Math.round(latestTbt)}ms` : null}
              delta={getDelta(tbt)}
              status={getCwvStatus(latestTbt, 200, 600)}
              accentBg="bg-sky-50"
              accentText="text-sky-600"
            />
          </div>

          {/* Performance Score Trend */}
          <ChartCard title={t("seo.performanceScore")} accentBorder="border-l-sky-500">
            <SeoPerformanceChart data={chart} />
          </ChartCard>

          {/* Core Web Vitals — individual mini charts */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <ChartCard title="LCP (Largest Contentful Paint)" accentBorder="border-l-sky-400">
              <CwvMiniChart
                data={chart.labels.map((label, i) => ({ date: label, value: (lcp as (number | null)[])[i] ?? null }))}
                label="LCP"
                color="#0ea5e9"
                thresholds={[2.5, 4]}
                unit="s"
              />
            </ChartCard>
            <ChartCard title="CLS (Cumulative Layout Shift)" accentBorder="border-l-violet-400">
              <CwvMiniChart
                data={chart.labels.map((label, i) => ({ date: label, value: (cls as (number | null)[])[i] ?? null }))}
                label="CLS"
                color="#8b5cf6"
                thresholds={[0.1, 0.25]}
                unit=""
              />
            </ChartCard>
            <ChartCard title="TBT (Total Blocking Time)" accentBorder="border-l-amber-400">
              <CwvMiniChart
                data={chart.labels.map((label, i) => ({ date: label, value: (tbt as (number | null)[])[i] ?? null }))}
                label="TBT"
                color="#f59e0b"
                thresholds={[200, 600]}
                unit="ms"
              />
            </ChartCard>
          </div>
        </div>
      )}
    </div>
  );
}

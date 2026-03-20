import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { useGeoChart } from "../hooks/useGeoData";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { EmptyState } from "../components/common/EmptyState";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { GeoScoreChart } from "../components/charts/GeoScoreChart";
import { useI18n } from "../i18n";

export function GeoPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: summary, isLoading: loadingSummary } = useProjectSummary(projectId);
  const { data: chart, isLoading: loadingChart } = useGeoChart(projectId);
  const { t } = useI18n();

  if (loadingSummary) return <LoadingSpinner />;
  if (!summary) return <ErrorAlert message={t("common.projectNotFound")} />;

  return (
    <div>
      <ProjectHeader project={summary.project} />
      <ProjectTabs projectId={projectId} />
      {loadingChart ? (
        <LoadingSpinner />
      ) : !chart?.labels?.length ? (
        <EmptyState title={t("geo.noData")} description={t("geo.noDataDesc")} />
      ) : (
        <div className="rounded-xl border bg-white p-4">
          <h3 className="mb-3 font-semibold">{t("geo.scoreTrend")}</h3>
          <GeoScoreChart data={chart} />
        </div>
      )}
    </div>
  );
}

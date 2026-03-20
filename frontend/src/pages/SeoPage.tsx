import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { useSeoChart } from "../hooks/useSeoData";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { EmptyState } from "../components/common/EmptyState";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { SeoPerformanceChart } from "../components/charts/SeoPerformanceChart";
import { CwvChart } from "../components/charts/CwvChart";
import { useI18n } from "../i18n";

export function SeoPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: summary, isLoading: loadingSummary } = useProjectSummary(projectId);
  const { data: chart, isLoading: loadingChart } = useSeoChart(projectId);
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
        <EmptyState title={t("seo.noData")} description={t("seo.noDataDesc")} />
      ) : (
        <div className="space-y-6">
          <div className="rounded-xl border bg-white p-4">
            <h3 className="mb-3 font-semibold">{t("seo.performanceScore")}</h3>
            <SeoPerformanceChart data={chart} />
          </div>
          <div className="rounded-xl border bg-white p-4">
            <h3 className="mb-3 font-semibold">{t("seo.coreWebVitals")}</h3>
            <CwvChart data={chart} />
          </div>
        </div>
      )}
    </div>
  );
}

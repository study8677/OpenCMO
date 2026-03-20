import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { useSerpLatest, useSerpChart } from "../hooks/useSerpData";
import { useKeywords, useAddKeyword, useDeleteKeyword } from "../hooks/useKeywords";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { KeywordList } from "../components/keywords/KeywordList";
import { AddKeywordForm } from "../components/keywords/AddKeywordForm";
import { SerpRankingChart } from "../components/charts/SerpRankingChart";
import { useI18n } from "../i18n";

export function SerpPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: summary, isLoading } = useProjectSummary(projectId);
  const { data: serpLatest } = useSerpLatest(projectId);
  const { data: serpChart } = useSerpChart(projectId);
  const { data: keywords } = useKeywords(projectId);
  const addKeyword = useAddKeyword(projectId);
  const deleteKeyword = useDeleteKeyword(projectId);
  const { t } = useI18n();

  if (isLoading) return <LoadingSpinner />;
  if (!summary) return <ErrorAlert message={t("common.projectNotFound")} />;

  return (
    <div>
      <ProjectHeader project={summary.project} />
      <ProjectTabs projectId={projectId} />
      <div className="space-y-6">
        <div className="rounded-xl border bg-white p-4">
          <h3 className="mb-3 font-semibold">{t("serp.trackedKeywords")}</h3>
          <AddKeywordForm
            onAdd={(kw) => addKeyword.mutate(kw)}
            isLoading={addKeyword.isPending}
          />
          <KeywordList
            keywords={keywords ?? []}
            serpData={serpLatest ?? []}
            onDelete={(kwId) => deleteKeyword.mutate(kwId)}
          />
        </div>
        {serpChart?.labels?.length ? (
          <div className="rounded-xl border bg-white p-4">
            <h3 className="mb-3 font-semibold">{t("serp.rankingHistory")}</h3>
            <SerpRankingChart data={serpChart} />
          </div>
        ) : null}
      </div>
    </div>
  );
}

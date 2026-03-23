import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { useGraphData, useExpansionStatus } from "../hooks/useGraphData";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { EmptyState } from "../components/common/EmptyState";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { KnowledgeGraph } from "../components/charts/KnowledgeGraph";
import { CompetitorPanel } from "../components/charts/CompetitorPanel";
import { ExpansionControls } from "../components/charts/ExpansionControls";
import { useI18n } from "../i18n";

export function GraphPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: summary, isLoading } = useProjectSummary(projectId);
  const { data: expansion } = useExpansionStatus(projectId);
  const isExpanding = expansion?.runtime_state === "running";
  const { data: graph, isLoading: loadingGraph } = useGraphData(projectId, isExpanding);
  const { t, locale } = useI18n();
  const isZh = locale === "zh";

  if (isLoading) return <LoadingSpinner />;
  if (!summary) return <ErrorAlert message={t("common.projectNotFound")} />;

  return (
    <div>
      <ProjectHeader project={summary.project} />
      <ProjectTabs projectId={projectId} />
      <div className="space-y-6">
        {/* Expansion controls */}
        <ExpansionControls projectId={projectId} />

        {/* Graph */}
        {loadingGraph ? (
          <LoadingSpinner />
        ) : !graph || graph.nodes.length === 0 ? (
          <EmptyState
            title={isZh ? "暂无图谱数据" : "No graph data yet"}
            description={isZh ? "运行扫描后，图谱将展示品牌、关键词、社区讨论和竞品之间的关系。" : "After running scans, the graph will show relationships between your brand, keywords, discussions, and competitors."}
          />
        ) : (
          <KnowledgeGraph data={graph} />
        )}

        {/* Competitor management */}
        <CompetitorPanel projectId={projectId} />
      </div>
    </div>
  );
}

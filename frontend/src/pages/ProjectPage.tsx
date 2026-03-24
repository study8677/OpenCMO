import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { ScorePanel } from "../components/project/ScorePanel";
import { ScanHistoryTable } from "../components/project/ScanHistoryTable";
import { NextActions } from "../components/project/NextActions";
import { CampaignTimeline } from "../components/project/CampaignTimeline";
import { useI18n } from "../i18n";

export function ProjectPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data, isLoading, error } = useProjectSummary(projectId);
  const { t } = useI18n();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error.message} />;
  if (!data) return <ErrorAlert message={t("common.projectNotFound")} />;

  const { project, latest, previous, latest_monitoring } = data;

  return (
    <div>
      <ProjectHeader project={project} />
      <ProjectTabs projectId={projectId} />
      <ScorePanel latest={latest} previous={previous} latestMonitoring={latest_monitoring} />
      <NextActions projectId={projectId} />
      <CampaignTimeline projectId={projectId} />
      <ScanHistoryTable latest={latest} />
    </div>
  );
}

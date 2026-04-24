import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { ScorePanel } from "../components/project/ScorePanel";
import { ScanHistoryTable } from "../components/project/ScanHistoryTable";
import { CampaignTimeline } from "../components/project/CampaignTimeline";
import { ActionFeed } from "../components/project/ActionFeed";
import { InsightBanner } from "../components/dashboard/InsightBanner";
import { useI18n } from "../i18n";
import { ProjectCommandCenter } from "../components/project/ProjectCommandCenter";
import { BlogGenerateButton } from "../components/project/BlogGenerateButton";

export function ProjectPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data, isLoading, error } = useProjectSummary(projectId);
  const { t } = useI18n();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error.message} />;
  if (!data) return <ErrorAlert message={t("common.projectNotFound")} />;

  const {
    project,
    latest,
    previous,
    latest_monitoring,
    latest_reports,
    is_paused,
    competitor_count,
    pending_approvals,
    blog_drafts_count,
  } = data;

  return (
    <div>
      <ProjectHeader project={project} isPaused={is_paused} />
      <InsightBanner projectId={projectId} />
      <ProjectTabs projectId={projectId} />

      <div className="mt-6 space-y-6">
        <ProjectCommandCenter
          projectId={projectId}
          latest={latest}
          latestMonitoring={latest_monitoring}
          latestReports={latest_reports}
          competitorCount={competitor_count}
          pendingApprovals={pending_approvals}
          blogDraftsCount={blog_drafts_count}
          contentAction={<BlogGenerateButton projectId={projectId} />}
        />

        <section className="rounded-3xl border border-slate-200/80 bg-white/90 p-6 shadow-sm">
          <ScorePanel latest={latest} previous={previous} latestMonitoring={latest_monitoring} />
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
          <section className="rounded-3xl border border-slate-200/80 bg-white/90 p-6 shadow-sm">
            <ActionFeed projectId={projectId} />
          </section>

          <div className="space-y-6">
            <section className="rounded-3xl border border-slate-200/80 bg-white/90 p-6 shadow-sm">
              <CampaignTimeline projectId={projectId} />
            </section>

            <details className="group rounded-3xl border border-slate-200/80 bg-white/90 p-6 shadow-sm">
              <summary className="cursor-pointer text-sm font-semibold text-slate-500 transition hover:text-slate-700">
                Scan History ▾
              </summary>
              <div className="mt-4">
                <ScanHistoryTable latest={latest} />
              </div>
            </details>
          </div>
        </div>
      </div>
    </div>
  );
}

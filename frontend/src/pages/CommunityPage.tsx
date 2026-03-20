import { useParams } from "react-router";
import { useProjectSummary } from "../hooks/useProject";
import { useDiscussions, useCommunityChart } from "../hooks/useCommunityData";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { EmptyState } from "../components/common/EmptyState";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { CommunityBarChart } from "../components/charts/CommunityBarChart";
import { ExternalLink } from "lucide-react";
import { useI18n } from "../i18n";

export function CommunityPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: summary, isLoading } = useProjectSummary(projectId);
  const { data: discussions } = useDiscussions(projectId);
  const { data: chart } = useCommunityChart(projectId);
  const { t } = useI18n();

  if (isLoading) return <LoadingSpinner />;
  if (!summary) return <ErrorAlert message={t("common.projectNotFound")} />;

  return (
    <div>
      <ProjectHeader project={summary.project} />
      <ProjectTabs projectId={projectId} />
      <div className="space-y-6">
        {chart?.scan_labels?.length ? (
          <div className="rounded-xl border bg-white p-4">
            <h3 className="mb-3 font-semibold">{t("community.scanHistory")}</h3>
            <CommunityBarChart data={chart} />
          </div>
        ) : null}
        <div className="rounded-xl border bg-white">
          <div className="border-b px-4 py-3">
            <h3 className="font-semibold">{t("community.trackedDiscussions")}</h3>
          </div>
          {!discussions?.length ? (
            <div className="p-4">
              <EmptyState title={t("community.noDiscussions")} description={t("community.noDiscussionsDesc")} />
            </div>
          ) : (
            <div className="divide-y">
              {discussions.map((d) => (
                <div key={d.id} className="flex items-center justify-between px-4 py-3">
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
                    <p className="text-xs text-gray-500">
                      {d.platform} &middot; {t("community.comments", { count: d.comments_count ?? 0 })} &middot; {t("community.engagement", { score: d.engagement_score ?? 0 })}
                    </p>
                  </div>
                  <span className="ml-3 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                    {d.platform}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

import { useState } from "react";
import { useCampaigns, useCampaign } from "../../hooks/useCampaigns";
import { useI18n } from "../../i18n";
import {
  Rocket, FileText, ChevronDown, ChevronUp, Clock,
  CheckCircle2, Loader2,
} from "lucide-react";

const STATUS_ICON: Record<string, React.ElementType> = {
  drafting: Loader2,
  completed: CheckCircle2,
};

const STATUS_STYLE: Record<string, string> = {
  drafting: "text-blue-600 bg-blue-50",
  completed: "text-emerald-600 bg-emerald-50",
  cancelled: "text-zinc-400 bg-zinc-50",
};

function ArtifactCard({ artifact }: { artifact: { artifact_type: string; channel: string | null; title: string; content: string } }) {
  const [expanded, setExpanded] = useState(false);
  const preview = artifact.content.slice(0, 200);

  return (
    <div className="rounded-lg border border-zinc-100 bg-white p-3">
      <div
        className="flex cursor-pointer items-center justify-between"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-indigo-400" />
          <span className="text-sm font-medium text-zinc-700">
            {artifact.title || artifact.artifact_type}
          </span>
          {artifact.channel && (
            <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-semibold text-zinc-500">
              {artifact.channel}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-zinc-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-zinc-400" />
        )}
      </div>
      <div className="mt-2 text-sm leading-relaxed text-zinc-500 whitespace-pre-wrap">
        {expanded ? artifact.content : preview + (artifact.content.length > 200 ? "..." : "")}
      </div>
    </div>
  );
}

function CampaignDetail({ runId }: { runId: number }) {
  const { data: run } = useCampaign(runId);
  if (!run?.artifacts) return null;

  return (
    <div className="mt-3 space-y-2 pl-8">
      {run.artifacts.map((a) => (
        <ArtifactCard key={a.id} artifact={a} />
      ))}
    </div>
  );
}

export function CampaignTimeline({ projectId }: { projectId: number }) {
  const { data: campaigns } = useCampaigns(projectId);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const { t } = useI18n();

  if (!campaigns || campaigns.length === 0) return null;

  return (
    <div className="mt-8">
      <h2 className="mb-4 flex items-center gap-2 text-lg font-bold text-zinc-800">
        <Rocket className="h-5 w-5 text-indigo-500" />
        {t("project.campaigns")}
      </h2>
      <div className="space-y-3">
        {campaigns.map((run) => {
          const StatusIcon = STATUS_ICON[run.status] ?? Clock;
          const isExpanded = expandedId === run.id;
          return (
            <div key={run.id}>
              <div
                className="flex cursor-pointer items-center gap-4 rounded-xl border border-zinc-100 bg-white p-4 transition hover:shadow-md"
                onClick={() => setExpandedId(isExpanded ? null : run.id)}
              >
                <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${STATUS_STYLE[run.status] ?? "bg-zinc-50"}`}>
                  <StatusIcon className={`h-4.5 w-4.5 ${run.status === "drafting" ? "animate-spin" : ""}`} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-zinc-800">{run.goal}</span>
                    <span className="text-xs text-zinc-400">{run.created_at?.slice(0, 10)}</span>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {run.channels.map((ch) => (
                      <span
                        key={ch}
                        className="rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-semibold text-indigo-600"
                      >
                        {ch}
                      </span>
                    ))}
                    {(run.artifact_count ?? 0) > 0 && (
                      <span className="text-[10px] text-zinc-400">
                        {run.artifact_count} {t("project.artifacts")}
                      </span>
                    )}
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronUp className="h-5 w-5 text-zinc-300" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-zinc-300" />
                )}
              </div>
              {isExpanded && <CampaignDetail runId={run.id} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}

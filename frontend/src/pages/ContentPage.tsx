import { useParams } from "react-router";
import { PenLine, FileText, Globe, Star } from "lucide-react";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { BlogGenerateButton } from "../components/project/BlogGenerateButton";
import { useBlogDrafts } from "../hooks/useBlogGen";
import { useProjectSummary } from "../hooks/useProject";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { useI18n } from "../i18n";
import type { MarketingSkillId } from "../types";
import type { TranslationKey } from "../i18n";

const SKILL_LABEL_KEYS: Record<MarketingSkillId, TranslationKey> = {
  content_strategy: "blogGen.skill.content_strategy",
  copywriting: "blogGen.skill.copywriting",
  ai_seo: "blogGen.skill.ai_seo",
  competitor_alternatives: "blogGen.skill.competitor_alternatives",
  programmatic_seo: "blogGen.skill.programmatic_seo",
  directory_submissions: "blogGen.skill.directory_submissions",
};

function ScoreBadge({ score, label }: { score: number; label: string }) {
  const color =
    score >= 80 ? "text-emerald-700 bg-emerald-50"
    : score >= 60 ? "text-amber-700 bg-amber-50"
    : "text-rose-700 bg-rose-50";
  return (
    <div className={`rounded-xl px-3 py-2 ${color}`}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] opacity-70">{label}</p>
      <p className="mt-0.5 text-lg font-bold">{score}</p>
    </div>
  );
}

export function ContentPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useProjectSummary(projectId);
  const { data: drafts, isLoading: draftsLoading } = useBlogDrafts(projectId);
  const { t } = useI18n();

  if (summaryLoading) return <LoadingSpinner />;
  if (summaryError) return <ErrorAlert message={summaryError.message} />;
  if (!summary) return <ErrorAlert message={t("common.projectNotFound")} />;

  const { project, is_paused } = summary;

  return (
    <div>
      <ProjectHeader project={project} isPaused={is_paused} />
      <ProjectTabs projectId={projectId} />

      <div className="space-y-6">
        {/* Generate section */}
        <section className="rounded-3xl border border-slate-200/80 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.06),_transparent_40%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-6 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
              <PenLine size={18} />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold tracking-tight text-slate-950">
                {t("blogGen.title")}
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                {t("agents.contentWhy")}
              </p>
              <div className="mt-4">
                <BlogGenerateButton projectId={projectId} />
              </div>
            </div>
          </div>
        </section>

        {/* Drafts list */}
        <section className="rounded-3xl border border-slate-200/80 bg-white/90 p-6 shadow-sm">
          <div className="mb-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
              {t("content.draftsTitle")}
            </p>
            <p className="mt-1 text-sm text-slate-600">{t("content.draftsSubtitle")}</p>
          </div>

          {draftsLoading ? (
            <div className="py-8 text-center text-sm text-slate-400">{t("common.noData")}</div>
          ) : !drafts?.length ? (
            <div className="rounded-2xl border border-dashed border-slate-200 py-10 text-center">
              <FileText size={32} className="mx-auto text-slate-300" />
              <p className="mt-3 text-sm text-slate-400">{t("content.noDrafts")}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {drafts.map((draft) => (
                <article
                  key={draft.id}
                  className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-colors hover:bg-slate-50/50"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-slate-900 truncate">
                          {draft.title || t("content.untitled")}
                        </h3>
                        <span className="shrink-0 rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500 uppercase">
                          {draft.style.replace("_", " ")}
                        </span>
                        {draft.meta?.marketing_skill?.id && (
                          <span className="shrink-0 rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                            {t(SKILL_LABEL_KEYS[draft.meta.marketing_skill.id])}
                          </span>
                        )}
                        <span className="shrink-0 flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500 uppercase">
                          <Globe size={10} />
                          {draft.language}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-slate-400">
                        {new Date(draft.created_at).toLocaleDateString()} &middot; {draft.status}
                        {draft.paired_draft_id && ` \u00b7 ${t("content.bilingual")}`}
                      </p>
                      {draft.content_preview && (
                        <p className="mt-2 text-xs leading-5 text-slate-500 line-clamp-2">
                          {draft.content_preview}
                        </p>
                      )}
                    </div>

                    {draft.quality_scores?.overall != null && (
                      <div className="shrink-0 flex items-center gap-1 rounded-xl bg-slate-50 px-2.5 py-1.5">
                        <Star size={12} className="text-amber-500" />
                        <span className="text-sm font-bold text-slate-800">
                          {draft.quality_scores.overall}
                        </span>
                      </div>
                    )}
                  </div>

                  {draft.quality_scores?.seo != null && (
                    <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-5">
                      <ScoreBadge score={draft.quality_scores.seo} label={t("blogGen.scores.seo")} />
                      <ScoreBadge score={draft.quality_scores.readability} label={t("blogGen.scores.readability")} />
                      <ScoreBadge score={draft.quality_scores.keyword_coverage} label={t("blogGen.scores.keywords")} />
                      <ScoreBadge score={draft.quality_scores.structure} label={t("blogGen.scores.structure")} />
                      {typeof draft.quality_scores.framework === "number" && (
                        <ScoreBadge score={draft.quality_scores.framework} label={t("blogGen.scores.framework")} />
                      )}
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

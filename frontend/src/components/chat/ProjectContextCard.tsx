import {
  Search,
  Globe,
  MessageCircle,
  TrendingUp,
  Target,
  AlertTriangle,
  Sparkles,
  ExternalLink,
  Tag,
} from "lucide-react";
import type { ChatProjectContext } from "../../api/chatContext";
import { useI18n } from "../../i18n";

function ScoreCard({
  label,
  value,
  icon: Icon,
  color,
  suffix,
}: {
  label: string;
  value: number | string | null;
  icon: typeof Search;
  color: string;
  suffix?: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
      <div
        className={`flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br ${color} text-white shadow-sm`}
      >
        <Icon size={16} />
      </div>
      <div className="min-w-0">
        <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
          {label}
        </p>
        <p className="text-lg font-bold text-slate-800">
          {value != null ? value : "—"}
          {suffix && value != null ? (
            <span className="text-sm font-normal text-slate-400">{suffix}</span>
          ) : null}
        </p>
      </div>
    </div>
  );
}

function SeverityDot({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-500",
    warning: "bg-amber-400",
    info: "bg-blue-400",
  };
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${colors[severity] ?? "bg-slate-300"}`}
    />
  );
}

export function ProjectContextCard({
  context,
  onSuggest,
}: {
  context: ChatProjectContext;
  onSuggest: (prompt: string) => void;
}) {
  const { locale } = useI18n();
  const isZh = locale === "zh";
  const { project, scores, keywords, competitors, keyword_gaps, findings } =
    context;

  const suggestions = [
    {
      label: isZh ? "全渠道营销方案" : "Full-channel strategy",
      prompt: isZh
        ? `针对 ${project.brand_name} 项目，制定一个全平台推广方案`
        : `Create a comprehensive marketing strategy for ${project.brand_name}`,
    },
    {
      label: isZh ? "竞品深度分析" : "Competitor deep-dive",
      prompt: isZh
        ? `深度分析 ${project.brand_name} 的竞争对手，给出差异化建议`
        : `Analyze competitors for ${project.brand_name} and suggest differentiation`,
    },
    {
      label: isZh ? "提升 AI 可见度" : "Improve AI visibility",
      prompt: isZh
        ? `如何提升 ${project.brand_name} 在 AI 搜索引擎中的可见度？`
        : `How can I improve ${project.brand_name}'s visibility in AI search engines?`,
    },
    {
      label: isZh ? "生成博客文章" : "Write a blog post",
      prompt: isZh
        ? `针对 ${project.brand_name} 项目，帮我写一篇 SEO 博客文章`
        : `Write an SEO blog article for ${project.brand_name}`,
    },
  ];

  return (
    <div className="animate-in fade-in slide-in-from-bottom-3 duration-500 space-y-4">
      {/* Header */}
      <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/80 to-violet-50/60 p-5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-indigo-500" />
              <p className="text-xs font-semibold uppercase tracking-widest text-indigo-500">
                {isZh ? "项目分析就绪" : "Project context loaded"}
              </p>
            </div>
            <h3 className="mt-2 text-xl font-bold text-slate-900">
              {project.brand_name}
            </h3>
            <div className="mt-1 flex items-center gap-2 text-sm text-slate-500">
              <a
                href={project.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 hover:text-indigo-600 transition-colors"
              >
                {project.url.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                <ExternalLink size={12} />
              </a>
              <span className="rounded-full bg-slate-200/60 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                {project.category}
              </span>
            </div>
          </div>
        </div>

        {/* AI greeting */}
        <div className="mt-4 rounded-xl bg-white/70 p-3 text-sm text-slate-600 leading-relaxed">
          🤖{" "}
          {isZh
            ? `我已了解 ${project.brand_name} 的最新监控数据。你可以让我生成任意平台的营销内容、分析竞品、或制定推广策略。`
            : `I have ${project.brand_name}'s latest monitoring data loaded. Ask me to create content for any platform, analyze competitors, or build a marketing strategy.`}
        </div>
      </div>

      {/* Score cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <ScoreCard
          label="SEO"
          value={
            scores.seo != null ? `${Math.round(scores.seo * 100)}%` : null
          }
          icon={Search}
          color="from-violet-500 to-purple-600"
        />
        <ScoreCard
          label="GEO"
          value={scores.geo}
          icon={Globe}
          color="from-cyan-500 to-blue-600"
          suffix="/100"
        />
        <ScoreCard
          label={isZh ? "社区讨论" : "Community"}
          value={scores.community_hits}
          icon={MessageCircle}
          color="from-pink-500 to-rose-600"
          suffix={isZh ? " 条" : " hits"}
        />
        <ScoreCard
          label="SERP"
          value={
            scores.serp_tracked > 0
              ? `${scores.serp_top10}/${scores.serp_tracked}`
              : null
          }
          icon={TrendingUp}
          color="from-emerald-500 to-teal-600"
          suffix={isZh ? " 进前10" : " in top 10"}
        />
      </div>

      {/* Keywords & Competitors */}
      <div className="grid gap-3 lg:grid-cols-2">
        {keywords.length > 0 && (
          <div className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
            <div className="mb-2 flex items-center gap-1.5">
              <Tag size={14} className="text-indigo-400" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {isZh ? "追踪关键词" : "Tracked Keywords"}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {keywords.map((kw) => (
                <span
                  key={kw}
                  className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700"
                >
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {competitors.length > 0 && (
          <div className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
            <div className="mb-2 flex items-center gap-1.5">
              <Target size={14} className="text-orange-400" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {isZh ? "竞品" : "Competitors"}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {competitors.map((c) => (
                <span
                  key={c.label}
                  className="rounded-full bg-orange-50 px-2.5 py-1 text-xs font-medium text-orange-700"
                >
                  {c.label}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Keyword gaps */}
      {keyword_gaps.length > 0 && (
        <div className="rounded-xl border border-amber-100 bg-amber-50/50 p-4">
          <div className="mb-2 flex items-center gap-1.5">
            <AlertTriangle size={14} className="text-amber-500" />
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-600">
              {isZh ? "关键词差距" : "Keyword Gaps"}
            </span>
            <span className="text-[11px] text-amber-500">
              {isZh ? "（竞品有，你没有）" : "(competitors have, you don't)"}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {keyword_gaps.map((gap) => (
              <span
                key={gap}
                className="rounded-full border border-amber-200 bg-white px-2.5 py-1 text-xs font-medium text-amber-800"
              >
                {gap}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Findings */}
      {findings.length > 0 && (
        <div className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            {isZh ? "最近发现" : "Recent Findings"}
          </p>
          <div className="space-y-1.5">
            {findings.map((f, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-slate-600">
                <SeverityDot severity={f.severity} />
                <span className="text-[11px] font-medium uppercase text-slate-400 w-14 shrink-0">
                  {f.domain}
                </span>
                {f.title}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick action suggestions */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          {isZh ? "快速开始" : "Quick Start"}
        </p>
        <div className="grid grid-cols-2 gap-2">
          {suggestions.map((s) => (
            <button
              key={s.label}
              onClick={() => onSuggest(s.prompt)}
              className="rounded-xl border border-slate-100 bg-white p-3 text-left text-sm font-medium text-slate-700 shadow-sm transition-all hover:border-indigo-200 hover:bg-indigo-50/50 hover:text-indigo-700 hover:shadow active:scale-[0.98]"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

import { useEffect } from "react";
import { X, Search, BarChart3, MessageCircle, Target, Bot, Loader2, CheckCircle } from "lucide-react";
import { useTaskPoll } from "../../hooks/useTasks";
import { useI18n } from "../../i18n";
import type { AnalysisProgress } from "../../types";

const ROLE_CONFIG: Record<string, { icon: typeof Search; label: string; labelZh: string; color: string }> = {
  system: { icon: Bot, label: "System", labelZh: "系统", color: "text-slate-500 bg-slate-50 ring-slate-200" },
  product_analyst: { icon: Search, label: "Product Analyst", labelZh: "产品分析师", color: "text-indigo-700 bg-indigo-50 ring-indigo-200" },
  seo_specialist: { icon: BarChart3, label: "SEO Specialist", labelZh: "SEO 专家", color: "text-emerald-700 bg-emerald-50 ring-emerald-200" },
  community_strategist: { icon: MessageCircle, label: "Community Strategist", labelZh: "社区运营", color: "text-amber-700 bg-amber-50 ring-amber-200" },
  strategy_director: { icon: Target, label: "Strategy Director", labelZh: "策略总监", color: "text-violet-700 bg-violet-50 ring-violet-200" },
};

const ROUND_LABELS = ["", "Round 1 — Initial Analysis", "Round 2 — Refinement", "Round 3 — Final Strategy"];
const ROUND_LABELS_ZH = ["", "第一轮 — 初步分析", "第二轮 — 深化讨论", "第三轮 — 最终策略"];

export function AnalysisDialog({
  taskId,
  url,
  onClose,
}: {
  taskId: string;
  url: string;
  onClose: () => void;
}) {
  const { data: task } = useTaskPoll(taskId);
  const { locale } = useI18n();
  const isZh = locale === "zh";

  const progress: AnalysisProgress[] = task?.progress ?? [];
  const isDone = task?.status === "completed" || task?.status === "failed";

  // Group progress by round
  const rounds = new Map<number, AnalysisProgress[]>();
  for (const p of progress) {
    const arr = rounds.get(p.round) ?? [];
    arr.push(p);
    rounds.set(p.round, arr);
  }

  // Auto-scroll to bottom
  useEffect(() => {
    const el = document.getElementById("analysis-scroll");
    if (el) el.scrollTop = el.scrollHeight;
  }, [progress.length]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="flex h-[80vh] w-full max-w-2xl flex-col rounded-2xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              {isZh ? "AI 策略分析" : "AI Strategy Analysis"}
            </h2>
            <p className="mt-0.5 text-xs text-slate-400 truncate max-w-md">{url}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        {/* Discussion body */}
        <div id="analysis-scroll" className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
          {progress.length === 0 && !isDone && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Loader2 size={32} className="mb-3 animate-spin text-indigo-400" />
              <p className="text-sm text-slate-400">
                {isZh ? "正在爬取网页内容..." : "Crawling webpage content..."}
              </p>
            </div>
          )}

          {[...rounds.entries()].map(([roundNum, items]) => (
            <div key={roundNum}>
              {roundNum > 0 && (
                <div className="mb-3 flex items-center gap-2">
                  <div className="h-px flex-1 bg-slate-100" />
                  <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                    {isZh ? ROUND_LABELS_ZH[roundNum] : ROUND_LABELS[roundNum]}
                  </span>
                  <div className="h-px flex-1 bg-slate-100" />
                </div>
              )}
              <div className="space-y-3">
                {items.map((p, i) => {
                  const cfg = ROLE_CONFIG[p.role] || ROLE_CONFIG.system!;
                  const Icon = cfg!.icon;
                  return (
                    <div key={`${roundNum}-${i}`} className={`rounded-xl p-4 ring-1 ring-inset ${cfg!.color}`}>
                      <div className="mb-1.5 flex items-center gap-2">
                        <Icon size={14} />
                        <span className="text-xs font-semibold">
                          {isZh ? cfg!.labelZh : cfg!.label}
                        </span>
                      </div>
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{p.content}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Scanning phase indicator */}
          {progress.length > 0 && !isDone && rounds.has(3) && (
            <div className="flex items-center gap-2 rounded-xl bg-indigo-50 px-4 py-3 text-sm text-indigo-600 ring-1 ring-inset ring-indigo-200">
              <Loader2 size={14} className="animate-spin" />
              {isZh ? "分析完成，正在执行扫描..." : "Analysis complete, running scan..."}
            </div>
          )}

          {!isDone && progress.length > 0 && !rounds.has(3) && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Loader2 size={14} className="animate-spin" />
              {isZh ? "讨论进行中..." : "Discussion in progress..."}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-100 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            {isDone ? (
              <>
                <CheckCircle size={14} className="text-emerald-500" />
                <span className={task?.status === "failed" ? "text-rose-500" : "text-emerald-600"}>
                  {task?.status === "failed"
                    ? (isZh ? "失败" : "Failed")
                    : (isZh ? "全部完成" : "All done")}
                </span>
              </>
            ) : (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>{progress.length} / 7 {isZh ? "步" : "steps"}</span>
              </>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-xl bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200"
          >
            {isDone ? (isZh ? "关闭" : "Close") : (isZh ? "后台运行" : "Run in background")}
          </button>
        </div>
      </div>
    </div>
  );
}

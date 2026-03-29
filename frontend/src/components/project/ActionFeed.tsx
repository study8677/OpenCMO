import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import {
  AlertTriangle, Info, AlertCircle, CheckCircle,
  Zap, FileCheck, Search, Sparkles,
} from "lucide-react";
import { apiJson } from "../../api/client";

interface ActionItem {
  type: "insight" | "approval" | "finding";
  id: number;
  severity: "critical" | "warning" | "info";
  title: string;
  summary: string;
  cta: "view_data" | "review_approval" | "generate_content" | "start_chat";
  action_route?: string;
  insight_id?: number;
  approval_id?: number;
  created_at: string;
}

const CTA_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string }> = {
  view_data: { label: "View Details", icon: Search, color: "bg-sky-500 hover:bg-sky-400 shadow-[0_8px_24px_rgba(14,165,233,0.25)]" },
  review_approval: { label: "Review Draft", icon: FileCheck, color: "bg-amber-500 hover:bg-amber-400 shadow-[0_8px_24px_rgba(245,158,11,0.25)]" },
  generate_content: { label: "Generate Fix", icon: Zap, color: "bg-violet-500 hover:bg-violet-400 shadow-[0_8px_24px_rgba(139,92,246,0.25)]" },
  start_chat: { label: "Discuss", icon: Sparkles, color: "bg-emerald-500 hover:bg-emerald-400 shadow-[0_8px_24px_rgba(16,185,129,0.25)]" },
};

const SEV_STYLES: Record<string, { border: string; icon: React.ElementType; iconColor: string }> = {
  critical: { border: "border-l-rose-500", icon: AlertCircle, iconColor: "text-rose-500" },
  warning: { border: "border-l-amber-500", icon: AlertTriangle, iconColor: "text-amber-500" },
  info: { border: "border-l-sky-500", icon: Info, iconColor: "text-sky-500" },
};

export function ActionFeed({ projectId }: { projectId: number }) {
  const navigate = useNavigate();
  const [items, setItems] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [quickLoading, setQuickLoading] = useState<number | null>(null);

  useEffect(() => {
    apiJson<ActionItem[]>(`/projects/${projectId}/action-feed`)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [projectId]);

  const handleCta = async (item: ActionItem) => {
    if (item.cta === "review_approval") {
      navigate("/approvals");
      return;
    }
    if (item.cta === "view_data" && item.action_route) {
      navigate(item.action_route);
      return;
    }
    if (item.cta === "generate_content" && item.insight_id) {
      setQuickLoading(item.id);
      try {
        await apiJson(`/projects/${projectId}/quick-generate`, {
          method: "POST",
          body: JSON.stringify({ insight_id: item.insight_id }),
        });
        navigate("/approvals");
      } catch {
        // ignore
      } finally {
        setQuickLoading(null);
      }
      return;
    }
    if (item.cta === "start_chat") {
      navigate("/chat");
      return;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-200 border-t-slate-600" />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-emerald-300 bg-emerald-50/50 p-8 text-center">
        <CheckCircle className="mx-auto h-10 w-10 text-emerald-400" />
        <h3 className="mt-3 text-sm font-semibold text-emerald-800">All clear! 🎉</h3>
        <p className="mt-1 text-xs text-emerald-600">
          No urgent actions right now. Your agents are monitoring and will alert you when
          something needs attention.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <Zap className="h-4.5 w-4.5 text-violet-500" />
        <h2 className="text-sm font-bold uppercase tracking-widest text-slate-600">
          Action Feed
        </h2>
        <span className="rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-bold text-violet-700">
          {items.length}
        </span>
      </div>

      {items.map((item) => {
        const sev = (SEV_STYLES[item.severity] ?? SEV_STYLES.info)!;
        const cta = (CTA_CONFIG[item.cta] ?? CTA_CONFIG.view_data)!;
        const CtaIcon = cta.icon;
        const SevIcon = sev.icon;
        const isLoading = quickLoading === item.id;

        return (
          <div
            key={`${item.type}-${item.id}`}
            className={`group rounded-2xl border border-slate-200/70 border-l-4 bg-white/90 p-4 shadow-sm backdrop-blur-sm transition-all hover:shadow-md ${sev.border}`}
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-50">
                <SevIcon size={16} className={sev.iconColor} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-slate-500">
                    {item.type}
                  </span>
                </div>
                <h3 className="mt-1 text-sm font-semibold text-slate-800 leading-snug">
                  {item.title}
                </h3>
                <p className="mt-0.5 text-xs text-slate-500 leading-relaxed line-clamp-2">
                  {item.summary}
                </p>
              </div>
              <button
                onClick={() => handleCta(item)}
                disabled={isLoading}
                className={`shrink-0 inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 active:scale-95 disabled:opacity-50 ${cta.color}`}
              >
                {isLoading ? (
                  <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                ) : (
                  <CtaIcon size={14} />
                )}
                {cta.label}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

import { useNextActions } from "../../hooks/useProject";
import { useI18n } from "../../i18n";
import {
  Search, Globe, Users, TrendingUp, GitBranch,
  AlertCircle, ArrowRight,
} from "lucide-react";

const ICONS: Record<string, React.ElementType> = {
  search: Search,
  globe: Globe,
  users: Users,
  "trending-up": TrendingUp,
  "git-branch": GitBranch,
};

const PRIORITY_STYLES: Record<string, string> = {
  high: "border-l-red-400 bg-red-50/50",
  medium: "border-l-amber-400 bg-amber-50/50",
  low: "border-l-blue-400 bg-blue-50/50",
};

const PRIORITY_BADGE: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-blue-100 text-blue-700",
};

export function NextActions({ projectId }: { projectId: number }) {
  const { data } = useNextActions(projectId);
  const { t } = useI18n();

  const actions = data?.actions ?? [];
  if (actions.length === 0) return null;

  return (
    <div className="mt-8">
      <h2 className="mb-4 flex items-center gap-2 text-lg font-bold text-zinc-800">
        <AlertCircle className="h-5 w-5 text-purple-500" />
        {t("project.nextActions")}
      </h2>
      <div className="space-y-3">
        {actions.map((action, i) => {
          const Icon = ICONS[action.icon] ?? ArrowRight;
          return (
            <div
              key={i}
              className={`flex items-start gap-4 rounded-xl border-l-4 p-4 transition-all hover:shadow-md ${PRIORITY_STYLES[action.priority] ?? ""}`}
            >
              <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white shadow-sm">
                <Icon className="h-4.5 w-4.5 text-zinc-600" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-zinc-800">{action.title}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${PRIORITY_BADGE[action.priority] ?? ""}`}>
                    {action.priority}
                  </span>
                </div>
                <p className="mt-1 text-sm leading-relaxed text-zinc-500">
                  {action.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

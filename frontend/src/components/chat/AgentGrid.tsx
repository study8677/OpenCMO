import {
  Twitter,
  MessageCircle,
  Linkedin,
  Rocket,
  Newspaper,
  PenTool,
  Search,
  Globe,
  Radio,
  Sparkles,
} from "lucide-react";
import { useI18n } from "../../i18n";

interface AgentCard {
  id: string;
  icon: typeof Twitter;
  color: string;
  labelEn: string;
  labelZh: string;
  descEn: string;
  descZh: string;
  prompt: string;
}

const AGENTS: AgentCard[] = [
  {
    id: "cmo",
    icon: Sparkles,
    color: "from-indigo-500 to-violet-500",
    labelEn: "CMO Agent",
    labelZh: "CMO 总管",
    descEn: "Full marketing strategy & multi-channel planning",
    descZh: "全渠道营销策略制定与规划",
    prompt: "",
  },
  {
    id: "twitter",
    icon: Twitter,
    color: "from-sky-400 to-blue-500",
    labelEn: "Twitter/X Expert",
    labelZh: "Twitter/X 专家",
    descEn: "Tweets, threads & engagement strategy",
    descZh: "推文、话题串和互动策略",
    prompt: "I want to create Twitter/X marketing content. Please hand off to the Twitter/X expert.",
  },
  {
    id: "reddit",
    icon: MessageCircle,
    color: "from-orange-400 to-red-500",
    labelEn: "Reddit Expert",
    labelZh: "Reddit 专家",
    descEn: "Authentic community posts & subreddit strategy",
    descZh: "社区帖子撰写和子版块策略",
    prompt: "I want to create Reddit posts. Please hand off to the Reddit expert.",
  },
  {
    id: "linkedin",
    icon: Linkedin,
    color: "from-blue-500 to-blue-700",
    labelEn: "LinkedIn Expert",
    labelZh: "LinkedIn 专家",
    descEn: "Professional posts & thought leadership",
    descZh: "专业帖子和行业领导力内容",
    prompt: "I want to create LinkedIn content. Please hand off to the LinkedIn expert.",
  },
  {
    id: "producthunt",
    icon: Rocket,
    color: "from-orange-500 to-amber-600",
    labelEn: "Product Hunt",
    labelZh: "Product Hunt",
    descEn: "Launch copy, taglines & maker comments",
    descZh: "产品上线文案、标语和制作者评论",
    prompt: "I want to prepare a Product Hunt launch. Please hand off to the Product Hunt expert.",
  },
  {
    id: "hackernews",
    icon: Newspaper,
    color: "from-orange-600 to-red-600",
    labelEn: "Hacker News",
    labelZh: "Hacker News",
    descEn: "Show HN posts for developer audience",
    descZh: "面向开发者的 Show HN 帖子",
    prompt: "I want to create a Hacker News Show HN post. Please hand off to the HN expert.",
  },
  {
    id: "blog",
    icon: PenTool,
    color: "from-emerald-500 to-teal-600",
    labelEn: "Blog / SEO Writer",
    labelZh: "博客 / SEO 写手",
    descEn: "Articles, SEO content & blog strategy",
    descZh: "文章撰写、SEO 内容和博客策略",
    prompt: "I want to create blog/SEO content. Please hand off to the Blog/SEO expert.",
  },
  {
    id: "seo",
    icon: Search,
    color: "from-violet-500 to-purple-600",
    labelEn: "SEO Auditor",
    labelZh: "SEO 审计",
    descEn: "Technical SEO analysis & recommendations",
    descZh: "技术 SEO 分析和优化建议",
    prompt: "I want a technical SEO audit. Please hand off to the SEO audit expert.",
  },
  {
    id: "geo",
    icon: Globe,
    color: "from-cyan-500 to-blue-600",
    labelEn: "AI Visibility (GEO)",
    labelZh: "AI 可见度 (GEO)",
    descEn: "Check brand mentions in AI search engines",
    descZh: "检查品牌在 AI 搜索引擎中的提及",
    prompt: "I want to check AI visibility / GEO score. Please hand off to the AI visibility expert.",
  },
  {
    id: "community",
    icon: Radio,
    color: "from-pink-500 to-rose-600",
    labelEn: "Community Monitor",
    labelZh: "社区监控",
    descEn: "Scan discussions on Reddit, HN & Dev.to",
    descZh: "扫描 Reddit、HN 和 Dev.to 上的讨论",
    prompt: "I want to monitor community discussions. Please hand off to the community monitor.",
  },
];

export function AgentGrid({ onSelect }: { onSelect: (prompt: string) => void }) {
  const { locale } = useI18n();
  const isZh = locale === "zh";

  return (
    <div>
      <div className="mb-6 text-center">
        <h2 className="text-lg font-semibold text-slate-900">
          {isZh ? "选择一个 AI 专家开始对话" : "Choose an AI expert to start"}
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          {isZh
            ? "或直接在下方输入任何问题，CMO 总管会自动分配给合适的专家"
            : "Or type anything below — the CMO will auto-route to the right expert"}
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
        {AGENTS.map((agent) => {
          const Icon = agent.icon;
          return (
            <button
              key={agent.id}
              onClick={() => {
                if (agent.prompt) {
                  onSelect(agent.prompt);
                }
              }}
              disabled={!agent.prompt}
              className="group flex flex-col items-start rounded-xl border border-slate-100 p-4 text-left transition-all duration-150 hover:border-slate-200 hover:bg-slate-50 hover:shadow-sm disabled:cursor-default disabled:hover:border-slate-100 disabled:hover:bg-transparent disabled:hover:shadow-none"
            >
              <div
                className={`mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br ${agent.color} text-white shadow-sm`}
              >
                <Icon size={16} />
              </div>
              <span className="text-sm font-semibold text-slate-800">
                {isZh ? agent.labelZh : agent.labelEn}
              </span>
              <span className="mt-0.5 text-[11px] leading-tight text-slate-400">
                {isZh ? agent.descZh : agent.descEn}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

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
  BookOpen,
  Camera,
  Hash,
  Code2,
  Coffee,
  MessageSquare,
  FileText,
  GitBranch,
  Zap,
  Briefcase,
  Rss,
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
  priority?: number; // 1-5 stars
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
  // ⭐⭐⭐⭐⭐ platforms
  {
    id: "ruanyifeng",
    icon: BookOpen,
    color: "from-amber-500 to-orange-600",
    labelEn: "阮一峰周刊",
    labelZh: "阮一峰周刊",
    descEn: "Tech weekly submission via GitHub Issue",
    descZh: "科技爱好者周刊 GitHub Issue 投稿",
    prompt: "我要给阮一峰科技爱好者周刊投稿。请交给阮一峰周刊专家。",
    priority: 5,
  },
  {
    id: "zhihu",
    icon: Hash,
    color: "from-blue-500 to-indigo-600",
    labelEn: "知乎",
    labelZh: "知乎",
    descEn: "Articles & Q&A for tech community",
    descZh: "知乎文章和问答内容创作",
    prompt: "我要创建知乎内容。请交给知乎专家。",
    priority: 5,
  },
  {
    id: "xiaohongshu",
    icon: Camera,
    color: "from-rose-400 to-pink-600",
    labelEn: "小红书",
    labelZh: "小红书",
    descEn: "Image-text notes for mass audience",
    descZh: "图文种草笔记创作",
    prompt: "我要创建小红书笔记。请交给小红书专家。",
    priority: 5,
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
    priority: 5,
  },
  // ⭐⭐⭐⭐ platforms
  {
    id: "hackernews",
    icon: Newspaper,
    color: "from-orange-600 to-red-600",
    labelEn: "Hacker News",
    labelZh: "Hacker News",
    descEn: "Show HN posts for developer audience",
    descZh: "面向开发者的 Show HN 帖子",
    prompt: "I want to create a Hacker News Show HN post. Please hand off to the HN expert.",
    priority: 4,
  },
  {
    id: "v2ex",
    icon: Code2,
    color: "from-zinc-600 to-slate-800",
    labelEn: "V2EX",
    labelZh: "V2EX",
    descEn: "Developer community posts (share/create)",
    descZh: "开发者社区发帖 (分享/创造)",
    prompt: "我要在 V2EX 发帖。请交给 V2EX 专家。",
    priority: 4,
  },
  {
    id: "juejin",
    icon: PenTool,
    color: "from-blue-400 to-cyan-500",
    labelEn: "掘金",
    labelZh: "掘金",
    descEn: "Technical blog articles & tutorials",
    descZh: "掘金技术博客文章",
    prompt: "我要写掘金技术文章。请交给掘金专家。",
    priority: 4,
  },
  // ⭐⭐⭐ platforms
  {
    id: "twitter",
    icon: Twitter,
    color: "from-sky-400 to-blue-500",
    labelEn: "Twitter/X Expert",
    labelZh: "Twitter/X 专家",
    descEn: "Tweets, threads & engagement strategy",
    descZh: "推文、话题串和互动策略",
    prompt: "I want to create Twitter/X marketing content. Please hand off to the Twitter/X expert.",
    priority: 3,
  },
  {
    id: "jike",
    icon: Coffee,
    color: "from-yellow-400 to-amber-500",
    labelEn: "即刻",
    labelZh: "即刻",
    descEn: "Indie dev & startup circle posts",
    descZh: "独立开发者 / 创业者圈子动态",
    prompt: "我要发即刻动态。请交给即刻专家。",
    priority: 3,
  },
  {
    id: "wechat",
    icon: MessageSquare,
    color: "from-green-500 to-emerald-600",
    labelEn: "微信公众号",
    labelZh: "微信公众号",
    descEn: "WeChat long-form tech articles",
    descZh: "微信公众号技术长文",
    prompt: "我要写微信公众号文章。请交给微信公众号专家。",
    priority: 3,
  },
  {
    id: "oschina",
    icon: Globe,
    color: "from-green-600 to-teal-700",
    labelEn: "OSChina",
    labelZh: "开源中国",
    descEn: "Open-source project listings",
    descZh: "开源项目收录和推荐文",
    prompt: "我要在 OSChina 收录项目。请交给 OSChina 专家。",
    priority: 3,
  },
  {
    id: "sspai",
    icon: Zap,
    color: "from-red-500 to-rose-600",
    labelEn: "少数派",
    labelZh: "少数派",
    descEn: "Tool reviews & productivity articles",
    descZh: "工具测评和效率文章投稿",
    prompt: "我要给少数派投稿。请交给少数派专家。",
    priority: 3,
  },
  {
    id: "devto",
    icon: Rss,
    color: "from-slate-700 to-zinc-900",
    labelEn: "Dev.to",
    labelZh: "Dev.to",
    descEn: "Developer blog articles & tutorials",
    descZh: "开发者博客文章和教程",
    prompt: "I want to write a Dev.to article. Please hand off to the Dev.to expert.",
    priority: 3,
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
    priority: 3,
  },
  // ⭐⭐ platforms
  {
    id: "gitcode",
    icon: GitBranch,
    color: "from-red-600 to-orange-700",
    labelEn: "GitCode",
    labelZh: "GitCode",
    descEn: "Repository mirror for CSDN users",
    descZh: "仓库镜像 + CSDN 配套文章",
    prompt: "我要在 GitCode 设置仓库。请交给 GitCode 专家。",
    priority: 2,
  },
  {
    id: "infoq",
    icon: Briefcase,
    color: "from-purple-600 to-indigo-700",
    labelEn: "InfoQ",
    labelZh: "InfoQ",
    descEn: "Enterprise-grade tech articles",
    descZh: "面向架构师的深度技术文章",
    prompt: "我要给 InfoQ 投稿。请交给 InfoQ 专家。",
    priority: 2,
  },
  // Other tools (no priority — utility agents)
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
    id: "blog",
    icon: FileText,
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

function PriorityStars({ count }: { count: number }) {
  return (
    <span className="text-[10px] text-amber-500 ml-1">
      {"★".repeat(count)}
    </span>
  );
}

export function AgentGrid({ onSelect, projectName }: { onSelect: (prompt: string) => void; projectName?: string | null }) {
  const { locale } = useI18n();
  const isZh = locale === "zh";

  // When a project is selected, prefix prompts with project name
  const buildPrompt = (basePrompt: string) => {
    if (!projectName || !basePrompt) return basePrompt;
    const prefix = isZh
      ? `针对 ${projectName} 项目，`
      : `For the ${projectName} project, `;
    return prefix + basePrompt;
  };

  // Special CMO prompt when project is selected
  const cmoPrompt = projectName
    ? (isZh
        ? `帮我分析 ${projectName} 项目的整体营销策略和当前状况`
        : `Analyze the overall marketing strategy and current status for ${projectName}`)
    : "";

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
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-4">
        {AGENTS.map((agent) => {
          const Icon = agent.icon;
          const resolvedPrompt = agent.id === "cmo"
            ? cmoPrompt
            : buildPrompt(agent.prompt);
          return (
            <button
              key={agent.id}
              onClick={() => {
                if (resolvedPrompt) {
                  onSelect(resolvedPrompt);
                }
              }}
              disabled={!resolvedPrompt}
              className="group flex flex-col items-start rounded-xl border border-slate-100 p-4 text-left transition-all duration-150 hover:border-slate-200 hover:bg-slate-50 hover:shadow-sm disabled:cursor-default disabled:hover:border-slate-100 disabled:hover:bg-transparent disabled:hover:shadow-none"
            >
              <div
                className={`mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br ${agent.color} text-white shadow-sm`}
              >
                <Icon size={16} />
              </div>
              <span className="text-sm font-semibold text-slate-800">
                {isZh ? agent.labelZh : agent.labelEn}
                {agent.priority && <PriorityStars count={agent.priority} />}
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

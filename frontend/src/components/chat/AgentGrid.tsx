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
import { resolveLocaleText, type Locale } from "../../i18n/locale";

type LocalizedText = Partial<Record<Locale, string>> & { en: string };

interface AgentCard {
  id: string;
  icon: typeof Twitter;
  color: string;
  labels: LocalizedText;
  descs: LocalizedText;
  prompts?: LocalizedText;
  priority?: number;
}

const AGENTS: AgentCard[] = [
  {
    id: "cmo",
    icon: Sparkles,
    color: "from-indigo-500 to-violet-500",
    labels: { en: "CMO Agent", zh: "CMO 总管", ja: "CMO エージェント", ko: "CMO 에이전트", es: "Agente CMO" },
    descs: {
      en: "Full marketing strategy and multi-channel planning",
      zh: "全渠道营销策略制定与规划",
      ja: "マーケティング戦略とマルチチャネル計画",
      ko: "전채널 마케팅 전략 수립",
      es: "Estrategia de marketing y planificación multicanal",
    },
  },
  {
    id: "ruanyifeng",
    icon: BookOpen,
    color: "from-amber-500 to-orange-600",
    labels: {
      en: "Ruanyifeng Weekly",
      zh: "阮一峰周刊",
      ja: "Ruanyifeng Weekly",
      ko: "Ruanyifeng Weekly",
      es: "Ruanyifeng Weekly",
    },
    descs: {
      en: "Prepare a GitHub Issue submission for the developer weekly roundup",
      zh: "准备科技爱好者周刊的 GitHub Issue 投稿",
      ja: "開発者向け週刊の GitHub Issue 投稿を準備します",
      ko: "개발자 주간지용 GitHub Issue 투고를 준비합니다",
      es: "Prepara un envío por GitHub Issue para el resumen semanal",
    },
    prompts: {
      en: "I want to prepare a submission for Ruanyifeng Weekly. Please hand off to the Ruanyifeng Weekly expert.",
      zh: "我要给阮一峰科技爱好者周刊投稿。请交给阮一峰周刊专家。",
      ja: "Ruanyifeng Weekly に投稿したいです。阮一峰周刊の専門エージェントに引き継いでください。",
      ko: "Ruanyifeng Weekly에 투고하고 싶습니다. 해당 전문가에게 넘겨 주세요.",
      es: "Quiero preparar una propuesta para Ruanyifeng Weekly. Pásala al especialista de Ruanyifeng Weekly.",
    },
    priority: 5,
  },
  {
    id: "zhihu",
    icon: Hash,
    color: "from-blue-500 to-indigo-600",
    labels: { en: "Zhihu", zh: "知乎", ja: "Zhihu", ko: "Zhihu", es: "Zhihu" },
    descs: {
      en: "Create articles and Q&A for the Chinese tech community",
      zh: "为中文技术社区创作文章和问答内容",
      ja: "中国語テックコミュニティ向けの記事と Q&A を作成します",
      ko: "중국어 기술 커뮤니티용 글과 Q&A를 만듭니다",
      es: "Crea artículos y respuestas para la comunidad tecnológica china",
    },
    prompts: {
      en: "I want to create Zhihu content. Please hand off to the Zhihu expert.",
      zh: "我要创建知乎内容。请交给知乎专家。",
      ja: "Zhihu 向けのコンテンツを作りたいです。Zhihu の専門エージェントに引き継いでください。",
      ko: "Zhihu용 콘텐츠를 만들고 싶습니다. Zhihu 전문가에게 넘겨 주세요.",
      es: "Quiero crear contenido para Zhihu. Pásalo al especialista de Zhihu.",
    },
    priority: 5,
  },
  {
    id: "xiaohongshu",
    icon: Camera,
    color: "from-rose-400 to-pink-600",
    labels: { en: "Xiaohongshu", zh: "小红书", ja: "Xiaohongshu", ko: "Xiaohongshu", es: "Xiaohongshu" },
    descs: {
      en: "Create image-first social posts for broad discovery",
      zh: "创作面向大众传播的图文内容",
      ja: "発見されやすい画像中心の投稿を作成します",
      ko: "대중 노출용 이미지 중심 게시물을 만듭니다",
      es: "Crea publicaciones visuales para ampliar el descubrimiento",
    },
    prompts: {
      en: "I want to create Xiaohongshu posts. Please hand off to the Xiaohongshu expert.",
      zh: "我要创建小红书笔记。请交给小红书专家。",
      ja: "Xiaohongshu の投稿を作りたいです。Xiaohongshu の専門エージェントに引き継いでください。",
      ko: "Xiaohongshu 게시물을 만들고 싶습니다. Xiaohongshu 전문가에게 넘겨 주세요.",
      es: "Quiero crear publicaciones para Xiaohongshu. Pásalo al especialista de Xiaohongshu.",
    },
    priority: 5,
  },
  {
    id: "producthunt",
    icon: Rocket,
    color: "from-orange-500 to-amber-600",
    labels: { en: "Product Hunt", zh: "Product Hunt", ja: "Product Hunt", ko: "Product Hunt", es: "Product Hunt" },
    descs: {
      en: "Launch copy, taglines, and maker comments",
      zh: "准备上线文案、标语和 maker 评论",
      ja: "ローンチ文案、タグライン、Maker コメントを準備します",
      ko: "런치 카피, 태그라인, 메이커 코멘트를 준비합니다",
      es: "Prepara copy de lanzamiento, eslóganes y comentarios del maker",
    },
    prompts: {
      en: "I want to prepare a Product Hunt launch. Please hand off to the Product Hunt expert.",
      zh: "我要准备 Product Hunt 发布。请交给 Product Hunt 专家。",
      ja: "Product Hunt のローンチ準備をしたいです。Product Hunt の専門エージェントに引き継いでください。",
      ko: "Product Hunt 출시를 준비하고 싶습니다. Product Hunt 전문가에게 넘겨 주세요.",
      es: "Quiero preparar un lanzamiento en Product Hunt. Pásalo al especialista de Product Hunt.",
    },
    priority: 5,
  },
  {
    id: "hackernews",
    icon: Newspaper,
    color: "from-orange-600 to-red-600",
    labels: { en: "Hacker News", zh: "Hacker News", ja: "Hacker News", ko: "Hacker News", es: "Hacker News" },
    descs: {
      en: "Write Show HN posts for a developer audience",
      zh: "为开发者受众准备 Show HN 帖子",
      ja: "開発者向けの Show HN 投稿を作成します",
      ko: "개발자 대상 Show HN 게시물을 작성합니다",
      es: "Redacta publicaciones Show HN para desarrolladores",
    },
    prompts: {
      en: "I want to create a Hacker News Show HN post. Please hand off to the HN expert.",
      zh: "我要创建 Hacker News 的 Show HN 帖子。请交给 HN 专家。",
      ja: "Hacker News の Show HN 投稿を作りたいです。HN 専門エージェントに引き継いでください。",
      ko: "Hacker News용 Show HN 게시물을 만들고 싶습니다. HN 전문가에게 넘겨 주세요.",
      es: "Quiero crear una publicación Show HN para Hacker News. Pásala al especialista de HN.",
    },
    priority: 4,
  },
  {
    id: "v2ex",
    icon: Code2,
    color: "from-zinc-600 to-slate-800",
    labels: { en: "V2EX", zh: "V2EX", ja: "V2EX", ko: "V2EX", es: "V2EX" },
    descs: {
      en: "Create posts for the Chinese developer community",
      zh: "为中文开发者社区准备发帖内容",
      ja: "中国語の開発者コミュニティ向け投稿を作成します",
      ko: "중국어 개발자 커뮤니티용 게시물을 준비합니다",
      es: "Crea publicaciones para la comunidad china de desarrolladores",
    },
    prompts: {
      en: "I want to publish on V2EX. Please hand off to the V2EX expert.",
      zh: "我要在 V2EX 发帖。请交给 V2EX 专家。",
      ja: "V2EX に投稿したいです。V2EX の専門エージェントに引き継いでください。",
      ko: "V2EX에 글을 올리고 싶습니다. V2EX 전문가에게 넘겨 주세요.",
      es: "Quiero publicar en V2EX. Pásalo al especialista de V2EX.",
    },
    priority: 4,
  },
  {
    id: "juejin",
    icon: PenTool,
    color: "from-blue-400 to-cyan-500",
    labels: { en: "Juejin", zh: "掘金", ja: "Juejin", ko: "Juejin", es: "Juejin" },
    descs: {
      en: "Write technical articles and tutorials for Chinese developers",
      zh: "为中文开发者编写技术文章和教程",
      ja: "中国語の開発者向け技術記事とチュートリアルを作成します",
      ko: "중국어 개발자를 위한 기술 글과 튜토리얼을 작성합니다",
      es: "Escribe artículos técnicos y tutoriales para desarrolladores chinos",
    },
    prompts: {
      en: "I want to write a technical article for Juejin. Please hand off to the Juejin expert.",
      zh: "我要写掘金技术文章。请交给掘金专家。",
      ja: "Juejin 向けの技術記事を書きたいです。Juejin の専門エージェントに引き継いでください。",
      ko: "Juejin용 기술 글을 쓰고 싶습니다. Juejin 전문가에게 넘겨 주세요.",
      es: "Quiero escribir un artículo técnico para Juejin. Pásalo al especialista de Juejin.",
    },
    priority: 4,
  },
  {
    id: "twitter",
    icon: Twitter,
    color: "from-sky-400 to-blue-500",
    labels: { en: "Twitter/X Expert", zh: "Twitter/X 专家", ja: "Twitter/X エキスパート", ko: "Twitter/X 전문가", es: "Experto Twitter/X" },
    descs: {
      en: "Tweets, threads, and engagement strategy",
      zh: "推文、线程和互动策略",
      ja: "ツイート、スレッド、エンゲージメント戦略",
      ko: "트윗, 스레드, 참여 전략",
      es: "Tweets, hilos y estrategia de engagement",
    },
    prompts: {
      en: "I want to create Twitter/X marketing content. Please hand off to the Twitter/X expert.",
      zh: "我要创建 Twitter/X 营销内容。请交给 Twitter/X 专家。",
      ja: "Twitter/X 向けのマーケティングコンテンツを作りたいです。Twitter/X の専門エージェントに引き継いでください。",
      ko: "Twitter/X용 마케팅 콘텐츠를 만들고 싶습니다. Twitter/X 전문가에게 넘겨 주세요.",
      es: "Quiero crear contenido de marketing para Twitter/X. Pásalo al especialista de Twitter/X.",
    },
    priority: 3,
  },
  {
    id: "jike",
    icon: Coffee,
    color: "from-yellow-400 to-amber-500",
    labels: { en: "Jike", zh: "即刻", ja: "Jike", ko: "Jike", es: "Jike" },
    descs: {
      en: "Write updates for indie developers and startup circles",
      zh: "为独立开发者和创业圈准备动态内容",
      ja: "インディー開発者とスタートアップ向けの投稿を作成します",
      ko: "인디 개발자와 스타트업 커뮤니티용 게시물을 작성합니다",
      es: "Crea actualizaciones para círculos indie y startups",
    },
    prompts: {
      en: "I want to publish on Jike. Please hand off to the Jike expert.",
      zh: "我要发即刻动态。请交给即刻专家。",
      ja: "Jike に投稿したいです。Jike の専門エージェントに引き継いでください。",
      ko: "Jike에 게시하고 싶습니다. Jike 전문가에게 넘겨 주세요.",
      es: "Quiero publicar en Jike. Pásalo al especialista de Jike.",
    },
    priority: 3,
  },
  {
    id: "wechat",
    icon: MessageSquare,
    color: "from-green-500 to-emerald-600",
    labels: {
      en: "WeChat Official Account",
      zh: "微信公众号",
      ja: "WeChat公式アカウント",
      ko: "WeChat 공식계정",
      es: "Cuenta oficial de WeChat",
    },
    descs: {
      en: "Long-form technical articles for WeChat",
      zh: "为微信公众号撰写技术长文",
      ja: "WeChat 向けの技術ロング記事を作成します",
      ko: "WeChat용 기술 장문 아티클을 작성합니다",
      es: "Crea artículos técnicos largos para WeChat",
    },
    prompts: {
      en: "I want to write a WeChat official account article. Please hand off to the WeChat expert.",
      zh: "我要写微信公众号文章。请交给微信公众号专家。",
      ja: "WeChat 公式アカウント向けの記事を書きたいです。WeChat の専門エージェントに引き継いでください。",
      ko: "WeChat 공식계정용 글을 쓰고 싶습니다. WeChat 전문가에게 넘겨 주세요.",
      es: "Quiero escribir un artículo para una cuenta oficial de WeChat. Pásalo al especialista de WeChat.",
    },
    priority: 3,
  },
  {
    id: "oschina",
    icon: Globe,
    color: "from-green-600 to-teal-700",
    labels: { en: "OSChina", zh: "开源中国", ja: "OSChina", ko: "OSChina", es: "OSChina" },
    descs: {
      en: "Prepare open-source listings and recommendation writeups",
      zh: "准备开源项目收录和推荐文案",
      ja: "オープンソース掲載と推薦文を準備します",
      ko: "오픈소스 등록과 추천 문안을 준비합니다",
      es: "Prepara listados open source y textos de recomendación",
    },
    prompts: {
      en: "I want to list this project on OSChina. Please hand off to the OSChina expert.",
      zh: "我要在 OSChina 收录项目。请交给 OSChina 专家。",
      ja: "このプロジェクトを OSChina に掲載したいです。OSChina の専門エージェントに引き継いでください。",
      ko: "이 프로젝트를 OSChina에 등록하고 싶습니다. OSChina 전문가에게 넘겨 주세요.",
      es: "Quiero listar este proyecto en OSChina. Pásalo al especialista de OSChina.",
    },
    priority: 3,
  },
  {
    id: "sspai",
    icon: Zap,
    color: "from-red-500 to-rose-600",
    labels: { en: "Shaoshu Pai", zh: "少数派", ja: "Shaoshu Pai", ko: "Shaoshu Pai", es: "Shaoshu Pai" },
    descs: {
      en: "Pitch tool reviews and productivity stories",
      zh: "准备工具测评和效率类投稿",
      ja: "ツールレビューと生産性記事の投稿を準備します",
      ko: "도구 리뷰와 생산성 콘텐츠 투고를 준비합니다",
      es: "Prepara reseñas de herramientas y artículos de productividad",
    },
    prompts: {
      en: "I want to pitch an article to Shaoshu Pai. Please hand off to the Shaoshu Pai expert.",
      zh: "我要给少数派投稿。请交给少数派专家。",
      ja: "Shaoshu Pai に寄稿したいです。Shaoshu Pai の専門エージェントに引き継いでください。",
      ko: "Shaoshu Pai에 투고하고 싶습니다. Shaoshu Pai 전문가에게 넘겨 주세요.",
      es: "Quiero proponer un artículo para Shaoshu Pai. Pásalo al especialista de Shaoshu Pai.",
    },
    priority: 3,
  },
  {
    id: "devto",
    icon: Rss,
    color: "from-slate-700 to-zinc-900",
    labels: { en: "Dev.to", zh: "Dev.to", ja: "Dev.to", ko: "Dev.to", es: "Dev.to" },
    descs: {
      en: "Write developer blog articles and tutorials",
      zh: "撰写面向开发者的博客文章和教程",
      ja: "開発者向け記事とチュートリアルを作成します",
      ko: "개발자용 블로그 글과 튜토리얼을 작성합니다",
      es: "Escribe artículos y tutoriales para desarrolladores",
    },
    prompts: {
      en: "I want to write a Dev.to article. Please hand off to the Dev.to expert.",
      zh: "我要写 Dev.to 文章。请交给 Dev.to 专家。",
      ja: "Dev.to の記事を書きたいです。Dev.to の専門エージェントに引き継いでください。",
      ko: "Dev.to 글을 쓰고 싶습니다. Dev.to 전문가에게 넘겨 주세요.",
      es: "Quiero escribir un artículo para Dev.to. Pásalo al especialista de Dev.to.",
    },
    priority: 3,
  },
  {
    id: "reddit",
    icon: MessageCircle,
    color: "from-orange-400 to-red-500",
    labels: { en: "Reddit Expert", zh: "Reddit 专家", ja: "Reddit エキスパート", ko: "Reddit 전문가", es: "Experto Reddit" },
    descs: {
      en: "Write authentic posts and subreddit strategy",
      zh: "撰写社区帖子并规划子版块策略",
      ja: "自然な投稿とサブレディット戦略を設計します",
      ko: "자연스러운 게시물과 서브레딧 전략을 설계합니다",
      es: "Diseña posts auténticos y estrategia de subreddit",
    },
    prompts: {
      en: "I want to create Reddit posts. Please hand off to the Reddit expert.",
      zh: "我要创建 Reddit 帖子。请交给 Reddit 专家。",
      ja: "Reddit 投稿を作りたいです。Reddit の専門エージェントに引き継いでください。",
      ko: "Reddit 게시물을 만들고 싶습니다. Reddit 전문가에게 넘겨 주세요.",
      es: "Quiero crear publicaciones para Reddit. Pásalo al especialista de Reddit.",
    },
    priority: 3,
  },
  {
    id: "gitcode",
    icon: GitBranch,
    color: "from-red-600 to-orange-700",
    labels: { en: "GitCode", zh: "GitCode", ja: "GitCode", ko: "GitCode", es: "GitCode" },
    descs: {
      en: "Mirror the repository and prepare companion content for CSDN users",
      zh: "配置仓库镜像并准备面向 CSDN 用户的配套内容",
      ja: "リポジトリミラーと CSDN 向け補助コンテンツを準備します",
      ko: "저장소 미러와 CSDN 사용자용 보조 콘텐츠를 준비합니다",
      es: "Replica el repositorio y prepara contenido para usuarios de CSDN",
    },
    prompts: {
      en: "I want to set up a GitCode repository mirror. Please hand off to the GitCode expert.",
      zh: "我要在 GitCode 设置仓库。请交给 GitCode 专家。",
      ja: "GitCode のリポジトリミラーを作りたいです。GitCode の専門エージェントに引き継いでください。",
      ko: "GitCode 저장소 미러를 설정하고 싶습니다. GitCode 전문가에게 넘겨 주세요.",
      es: "Quiero configurar un mirror del repositorio en GitCode. Pásalo al especialista de GitCode.",
    },
    priority: 2,
  },
  {
    id: "infoq",
    icon: Briefcase,
    color: "from-purple-600 to-indigo-700",
    labels: { en: "InfoQ", zh: "InfoQ", ja: "InfoQ", ko: "InfoQ", es: "InfoQ" },
    descs: {
      en: "Pitch enterprise-grade technical articles",
      zh: "准备面向架构师和技术负责人群的深度文章",
      ja: "エンタープライズ向け技術記事を企画します",
      ko: "엔터프라이즈 기술 아티클을 기획합니다",
      es: "Propone artículos técnicos de nivel empresarial",
    },
    prompts: {
      en: "I want to pitch an article to InfoQ. Please hand off to the InfoQ expert.",
      zh: "我要给 InfoQ 投稿。请交给 InfoQ 专家。",
      ja: "InfoQ に寄稿したいです。InfoQ の専門エージェントに引き継いでください。",
      ko: "InfoQ에 투고하고 싶습니다. InfoQ 전문가에게 넘겨 주세요.",
      es: "Quiero proponer un artículo para InfoQ. Pásalo al especialista de InfoQ.",
    },
    priority: 2,
  },
  {
    id: "linkedin",
    icon: Linkedin,
    color: "from-blue-500 to-blue-700",
    labels: { en: "LinkedIn Expert", zh: "LinkedIn 专家", ja: "LinkedIn エキスパート", ko: "LinkedIn 전문가", es: "Experto LinkedIn" },
    descs: {
      en: "Professional posts and thought leadership",
      zh: "准备专业帖子和行业观点内容",
      ja: "プロフェッショナル投稿とソートリーダーシップ",
      ko: "전문 게시물과 사고 리더십 콘텐츠",
      es: "Posts profesionales y liderazgo de opinión",
    },
    prompts: {
      en: "I want to create LinkedIn content. Please hand off to the LinkedIn expert.",
      zh: "我要创建 LinkedIn 内容。请交给 LinkedIn 专家。",
      ja: "LinkedIn 向けコンテンツを作りたいです。LinkedIn の専門エージェントに引き継いでください。",
      ko: "LinkedIn 콘텐츠를 만들고 싶습니다. LinkedIn 전문가에게 넘겨 주세요.",
      es: "Quiero crear contenido para LinkedIn. Pásalo al especialista de LinkedIn.",
    },
  },
  {
    id: "blog",
    icon: FileText,
    color: "from-emerald-500 to-teal-600",
    labels: { en: "Blog / SEO Writer", zh: "博客 / SEO 写手", ja: "ブログ / SEO ライター", ko: "블로그 / SEO 라이터", es: "Escritor Blog / SEO" },
    descs: {
      en: "Write articles, SEO content, and blog strategy",
      zh: "撰写文章、SEO 内容和博客策略",
      ja: "記事、SEO コンテンツ、ブログ戦略を作成します",
      ko: "기사, SEO 콘텐츠, 블로그 전략을 작성합니다",
      es: "Escribe artículos, contenido SEO y estrategia de blog",
    },
    prompts: {
      en: "I want to create blog and SEO content. Please hand off to the Blog/SEO expert.",
      zh: "我要创建博客和 SEO 内容。请交给博客 / SEO 专家。",
      ja: "ブログと SEO コンテンツを作りたいです。ブログ / SEO 専門エージェントに引き継いでください。",
      ko: "블로그와 SEO 콘텐츠를 만들고 싶습니다. 블로그/SEO 전문가에게 넘겨 주세요.",
      es: "Quiero crear contenido de blog y SEO. Pásalo al especialista de Blog/SEO.",
    },
  },
  {
    id: "seo",
    icon: Search,
    color: "from-violet-500 to-purple-600",
    labels: { en: "SEO Auditor", zh: "SEO 审计", ja: "SEO 監査", ko: "SEO 감사", es: "Auditor SEO" },
    descs: {
      en: "Run technical SEO analysis and recommendations",
      zh: "执行技术 SEO 分析并给出优化建议",
      ja: "テクニカル SEO 分析と改善提案を行います",
      ko: "기술 SEO 분석과 개선 권고를 제공합니다",
      es: "Ejecuta análisis SEO técnico y recomendaciones",
    },
    prompts: {
      en: "I want a technical SEO audit. Please hand off to the SEO audit expert.",
      zh: "我要做技术 SEO 审计。请交给 SEO 审计专家。",
      ja: "テクニカル SEO 監査をしたいです。SEO 監査専門エージェントに引き継いでください。",
      ko: "기술 SEO 감사를 하고 싶습니다. SEO 감사 전문가에게 넘겨 주세요.",
      es: "Quiero una auditoría SEO técnica. Pásala al especialista en auditoría SEO.",
    },
  },
  {
    id: "geo",
    icon: Globe,
    color: "from-cyan-500 to-blue-600",
    labels: { en: "AI Visibility (GEO)", zh: "AI 可见度 (GEO)", ja: "AI 可視性 (GEO)", ko: "AI 가시성 (GEO)", es: "Visibilidad IA (GEO)" },
    descs: {
      en: "Check brand mentions in AI search engines",
      zh: "检查品牌在 AI 搜索引擎中的提及情况",
      ja: "AI 検索エンジンでのブランド言及を確認します",
      ko: "AI 검색 엔진에서 브랜드 언급을 확인합니다",
      es: "Verifica menciones de la marca en buscadores de IA",
    },
    prompts: {
      en: "I want to check AI visibility and GEO score. Please hand off to the AI visibility expert.",
      zh: "我要检查 AI 可见度和 GEO 分数。请交给 AI 可见度专家。",
      ja: "AI 可視性と GEO スコアを確認したいです。AI 可視性専門エージェントに引き継いでください。",
      ko: "AI 가시성과 GEO 점수를 확인하고 싶습니다. AI 가시성 전문가에게 넘겨 주세요.",
      es: "Quiero revisar la visibilidad en IA y el puntaje GEO. Pásalo al especialista en visibilidad IA.",
    },
  },
  {
    id: "community",
    icon: Radio,
    color: "from-pink-500 to-rose-600",
    labels: { en: "Community Monitor", zh: "社区监控", ja: "コミュニティモニター", ko: "커뮤니티 모니터", es: "Monitor de Comunidad" },
    descs: {
      en: "Scan discussions on Reddit, HN, and Dev.to",
      zh: "扫描 Reddit、HN 和 Dev.to 上的讨论",
      ja: "Reddit、HN、Dev.to の議論をスキャンします",
      ko: "Reddit, HN, Dev.to 토론을 스캔합니다",
      es: "Escanea discusiones en Reddit, HN y Dev.to",
    },
    prompts: {
      en: "I want to monitor community discussions. Please hand off to the community monitor.",
      zh: "我要监控社区讨论。请交给社区监控专家。",
      ja: "コミュニティの議論を監視したいです。コミュニティ監視エージェントに引き継いでください。",
      ko: "커뮤니티 토론을 모니터링하고 싶습니다. 커뮤니티 모니터 전문가에게 넘겨 주세요.",
      es: "Quiero monitorear las discusiones de la comunidad. Pásalo al especialista de comunidad.",
    },
  },
];

function PriorityStars({ count }: { count: number }) {
  return <span className="ml-1 text-[10px] text-amber-500">{"★".repeat(count)}</span>;
}

export function AgentGrid({
  onSelect,
  projectName,
}: {
  onSelect: (prompt: string) => void;
  projectName?: string | null;
}) {
  const { locale, t } = useI18n();

  const buildPrompt = (basePrompt: string) => {
    if (!projectName || !basePrompt) return basePrompt;
    return t("agentGrid.projectPrefix", { name: projectName }) + basePrompt;
  };

  const cmoPrompt = projectName ? t("agentGrid.cmoPrompt", { name: projectName }) : "";

  return (
    <div>
      <div className="mb-6 text-center">
        <h2 className="text-lg font-semibold text-slate-900">{t("agentGrid.title")}</h2>
        <p className="mt-1 text-sm text-slate-400">{t("agentGrid.subtitle")}</p>
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-4">
        {AGENTS.map((agent) => {
          const Icon = agent.icon;
          const resolvedPrompt = agent.id === "cmo"
            ? cmoPrompt
            : buildPrompt(resolveLocaleText(locale, agent.prompts ?? { en: "" }));

          return (
            <button
              key={agent.id}
              onClick={() => {
                if (resolvedPrompt) onSelect(resolvedPrompt);
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
                {resolveLocaleText(locale, agent.labels)}
                {agent.priority ? <PriorityStars count={agent.priority} /> : null}
              </span>
              <span className="mt-0.5 text-[11px] leading-tight text-slate-400">
                {resolveLocaleText(locale, agent.descs)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

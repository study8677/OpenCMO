import type { TranslationKey } from "./en";

export const zh: Record<TranslationKey, string> = {
  // Common
  "common.cancel": "取消",
  "common.confirm": "确认",
  "common.logout": "退出登录",
  "common.noData": "暂无数据",
  "common.error": "错误",
  "common.never": "从未",
  "common.projectNotFound": "未找到项目",

  // Nav / Sidebar
  "nav.dashboard": "仪表盘",
  "nav.approvals": "审批流",
  "nav.monitors": "监控",
  "nav.aiChat": "AI 对话",
  "nav.projects": "项目",

  // Auth
  "auth.enterToken": "请输入访问令牌以继续。",
  "auth.tokenPlaceholder": "令牌",
  "auth.loggingIn": "登录中...",
  "auth.login": "登录",
  "auth.invalidToken": "无效令牌",

  // Dashboard
  "dashboard.title": "仪表盘",
  "dashboard.newMonitor": "新建监控",
  "dashboard.noProjects": "暂无项目",
  "dashboard.noProjectsDesc": "输入网站 URL 即可开始监控您的品牌在线表现。",
  "dashboard.createMonitor": "添加网站",
  "insights.title": "洞察",
  "insights.proactive": "主动洞察",
  "insights.topUnread": "重点未读提醒",
  "insights.empty": "暂无新洞察",
  "insights.loading": "正在加载洞察...",
  "insights.view": "查看",
  "insights.dismiss": "忽略",

  // Project Tabs
  "project.overview": "概览",
  "project.seo": "SEO",
  "project.geo": "GEO",
  "project.serp": "SERP",
  "project.community": "社区",
  "project.graph": "知识图谱",

  // Score Panel
  "score.seoScore": "SEO 评分",
  "score.geoScore": "GEO 评分",
  "score.communityHits": "社区命中",
  "score.serpKeywords": "SERP 关键词",
  "score.findings": "发现项",
  "score.recommendations": "行动建议",
  "score.tracked": "{{count}} 个跟踪中",

  // Next Best Actions
  "project.nextActions": "下一步行动建议",

  // Campaigns
  "project.campaigns": "营销战役",
  "project.artifacts": "个产物",

  // Global Overview
  "overview.avgSeo": "平均 SEO 分",
  "overview.avgGeo": "平均 GEO 分",
  "overview.communityHits": "社区讨论数",
  "overview.keywords": "追踪关键词",
  "overview.competitors": "竞品数量",
  "overview.campaigns": "营销战役",

  // Scan History
  "scan.latestScans": "最近扫描",
  "scan.type": "类型",
  "scan.lastScanned": "上次扫描",
  "scan.result": "结果",
  "scan.hits": "{{count}} 次命中",

  // SEO Page
  "seo.noData": "暂无 SEO 数据",
  "seo.noDataDesc": "运行扫描以查看 SEO 指标。",
  "seo.performanceScore": "性能评分",
  "seo.coreWebVitals": "核心 Web 指标",

  // GEO Page
  "geo.noData": "暂无 GEO 数据",
  "geo.noDataDesc": "运行扫描以查看 AI 可见度指标。",
  "geo.scoreTrend": "GEO 评分趋势",

  // SERP Page
  "serp.trackedKeywords": "跟踪关键词",
  "serp.rankingHistory": "排名历史",

  // Community Page
  "community.scanHistory": "扫描历史",
  "community.trackedDiscussions": "跟踪的讨论",
  "community.noDiscussions": "未找到讨论",
  "community.noDiscussionsDesc": "运行社区扫描以发现相关讨论。",
  "community.comments": "{{count}} 条评论",
  "community.engagement": "互动度: {{score}}",
  "community.platform.reddit": "Reddit",
  "community.platform.hackernews": "Hacker News",
  "community.platform.devto": "Dev.to",
  "community.platform.youtube": "YouTube",
  "community.platform.bluesky": "Bluesky",
  "community.platform.twitter": "Twitter/X",

  // Monitors Page
  "monitors.title": "监控",
  "monitors.newMonitor": "新建监控",
  "monitors.noMonitors": "暂无监控",
  "monitors.noMonitorsDesc": "在上方输入网站 URL 即可开始监控。",

  // Monitor Form
  "monitorForm.urlPlaceholder": "https://your-website.com",
  "monitorForm.subtitle": "AI 将自动分析您的品牌、SEO、社区可见度等。",
  "monitorForm.analyzing": "分析中...",
  "monitorForm.startMonitoring": "开始监控",

  // Monitor List
  "monitorList.brand": "品牌",
  "monitorList.type": "类型",
  "monitorList.cron": "Cron",
  "monitorList.lastRun": "上次运行",
  "monitorList.actions": "操作",
  "monitorList.schedule": "计划",
  "monitorList.fullScan": "完整扫描",

  // Run Scan
  "runScan.running": "运行中...",
  "runScan.done": "完成",
  "runScan.failed": "失败",
  "runScan.run": "运行",

  // Keywords
  "keywords.addPlaceholder": "添加关键词...",
  "keywords.add": "添加",
  "keywords.noKeywords": "暂无跟踪的关键词。",
  "keywords.keyword": "关键词",
  "keywords.position": "排名",
  "keywords.lastChecked": "上次检查",

  // Project Card
  "projectCard.hits": "{{count}} 次命中",
  "projectCard.kw": "{{count}} 个关键词",

  // Chat
  "chat.title": "AI 对话",
  "chat.agent": "代理: {{name}}",
  "chat.newChat": "新对话",
  "chat.placeholder": "输入消息...",
  "chat.emptyState": "询问关于您的营销策略的任何问题...",
  "chat.thinking": "思考中...",
  "chat.today": "今天",
  "chat.yesterday": "昨天",
  "chat.older": "更早",
  "chat.noHistory": "暂无对话记录",

  // Settings
  "settings.title": "设置",
  "settings.apiKey": "API 密钥",
  "settings.apiKeyPlaceholder": "sk-...",
  "settings.apiKeyHint": "您的 OpenAI 兼容 API 密钥，保存在服务端。",
  "settings.baseUrl": "Base URL（可选）",
  "settings.baseUrlPlaceholder": "https://api.openai.com/v1",
  "settings.baseUrlHint": "用于自定义服务商，如 DeepSeek、NVIDIA、Ollama 等。",
  "settings.model": "模型（可选）",
  "settings.modelPlaceholder": "gpt-4o",
  "settings.modelHint": "覆盖默认模型。",
  "settings.save": "保存",
  "settings.saved": "已保存！",
  "settings.apiKeySet": "API 密钥已配置",
  "settings.apiKeyNotSet": "未配置 API 密钥",

  // Settings — shared
  "settings.configured": "已配置",
  "settings.notConfigured": "未配置",

  // Settings — Reddit
  "settings.redditSection": "Reddit 发布",
  "settings.redditClientId": "Client ID",
  "settings.redditClientIdPlaceholder": "你的 Reddit 应用 Client ID",
  "settings.redditClientSecret": "Client Secret",
  "settings.redditClientSecretPlaceholder": "你的 Reddit 应用 Secret",
  "settings.redditUsername": "Reddit 用户名",
  "settings.redditUsernamePlaceholder": "你的 Reddit 用户名",
  "settings.redditPassword": "Reddit 密码",
  "settings.redditPasswordPlaceholder": "你的 Reddit 密码",
  "settings.redditHint": "在 reddit.com/prefs/apps 创建应用（类型选 script）。",
  "settings.redditConfigured": "Reddit 已连接",
  "settings.redditNotConfigured": "Reddit 未连接",
  "settings.autoPublish": "自动发布",
  "settings.autoPublishHint": "允许 AI 向 Reddit 和 Twitter 发布帖子和回复。",

  // Settings — Twitter
  "settings.twitterSection": "Twitter / X 发布",
  "settings.twitterApiKey": "API Key",
  "settings.twitterApiSecret": "API Secret",
  "settings.twitterAccessToken": "Access Token",
  "settings.twitterAccessSecret": "Access Token Secret",
  "settings.twitterHint": "在 developer.twitter.com 创建应用并开启读写权限。",
  "settings.twitterConfigured": "Twitter 已连接",
  "settings.twitterNotConfigured": "Twitter 未连接",

  // Settings — GEO
  "settings.geoSection": "GEO 检测平台",
  "settings.anthropicKey": "Anthropic API Key（Claude）",
  "settings.googleAiKey": "Google AI API Key（Gemini）",
  "settings.geoChatgpt": "启用 ChatGPT GEO",
  "settings.geoChatgptHint": "使用你的 OpenAI API 密钥检测 ChatGPT 中的品牌可见度。",
  "settings.geoHint": "启用更多平台以获得更全面的 AI 可见度覆盖。Perplexity 和 You.com 无需密钥即可使用。",

  // Settings — SEO
  "settings.seoSection": "SEO 增强",
  "settings.pagespeedKey": "Google PageSpeed API Key",
  "settings.pagespeedHint": "无密钥也可使用，但有速率限制。",
  "settings.pagespeedNotConfigured": "PageSpeed API 密钥未设置（限速模式）",

  // Settings — Tavily Search
  "settings.tavilySection": "网络搜索 (Tavily)",
  "settings.tavilyKey": "Tavily API Key",
  "settings.tavilyHint": "启用高质量网络搜索，用于博客研究、图谱扩展、SERP 追踪和 Agent 搜索回退。在 tavily.com 获取密钥。",
  "settings.tavilyNotConfigured": "Tavily 未配置（使用 Google 爬取回退）",

  // Settings — SERP
  "settings.serpSection": "SERP 排名追踪",
  "settings.dataforseoLogin": "DataForSEO 登录名",
  "settings.dataforseoPassword": "DataForSEO 密码",
  "settings.dataforseoHint": "关键词排名数据的替代来源（默认使用 Google 爬取）。",
  "settings.dataforseoNotConfigured": "DataForSEO 未配置（使用 Google 爬取）",

  // Settings — Email
  "settings.emailSection": "邮件报告",
  "settings.smtpHost": "SMTP 服务器",
  "settings.smtpPort": "SMTP 端口",
  "settings.smtpUser": "SMTP 用户名",
  "settings.smtpPass": "SMTP 密码",
  "settings.reportEmail": "报告接收邮箱",
  "settings.reportEmailHint": "接收监控报告的邮箱地址。",
  "settings.emailConfigured": "邮件已配置",
  "settings.emailNotConfigured": "邮件未配置",

  // Schedule presets
  "schedule.label": "监控频率",
  "schedule.hourly": "每小时",
  "schedule.every6h": "每6小时",
  "schedule.daily": "每天",
  "schedule.weekly": "每周",
  "schedule.monthly": "每月",
  "schedule.custom": "自定义",
  "schedule.enable": "启用定时",
  "schedule.disable": "暂停定时",

  // Knowledge Graph
  "graph.title": "知识图谱",
  "graph.noData": "暂无图谱数据",
  "graph.noDataDesc": "运行扫描后，图谱将展示品牌、关键词、社区讨论和竞品之间的关系。",
  "graph.competitors": "竞品",
  "graph.addCompetitor": "添加竞品",
  "graph.competitorName": "竞品名称",
  "graph.competitorUrl": "网址（可选）",
  "graph.competitorKw": "关键词，逗号分隔（可选）",
  "graph.noCompetitors": "暂无竞品。添加竞品后图谱将显示竞品节点。",

  // Graph Expansion
  "graph.expansion": "图谱扩展",
  "graph.startExploring": "开始探索",
  "graph.pause": "暂停",
  "graph.resume": "继续",
  "graph.reset": "重置",
  "graph.wave": "第 {{n}} 波",
  "graph.discovered": "已发现 {{count}} 个",
  "graph.explored": "已探索 {{count}} 个",
  "graph.expanding": "扩展中...",
  "graph.paused": "已暂停",
  "graph.interrupted": "已中断",
  "graph.pausingHint": "正在完成当前操作...",
  "graph.resetConfirm": "重置将清除深度追踪信息。已发现的数据将保留在图谱中，但深度信息将丢失。",
  "graph.noFrontier": "没有更多节点可探索。",
};

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

  // Project Tabs
  "project.overview": "概览",
  "project.seo": "SEO",
  "project.geo": "GEO",
  "project.serp": "SERP",
  "project.community": "社区",

  // Score Panel
  "score.seoScore": "SEO 评分",
  "score.geoScore": "GEO 评分",
  "score.communityHits": "社区命中",
  "score.serpKeywords": "SERP 关键词",
  "score.tracked": "{{count}} 个跟踪中",

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
};

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
  "project.reports": "报告",
  "project.brandKit": "品牌套件",
  "project.performance": "效果追踪",
  "project.seo": "SEO",
  "project.geo": "GEO",
  "project.serp": "SERP",
  "project.community": "社区",
  "project.graph": "知识图谱",
  "project.monitors": "监控运行",

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
  "overview.recentCampaigns": "最近战役",

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
  "runScan.viewResults": "查看结果",
  "runScan.rerun": "重新运行",
  "runHistory.title": "运行历史",
  "runHistory.loading": "正在加载运行历史...",
  "runHistory.empty": "暂无运行记录",
  "runHistory.findings": "发现项",
  "runHistory.recommendations": "建议项",
  "runHistory.status.pending": "排队中",
  "runHistory.status.running": "运行中",
  "runHistory.status.completed": "已完成",
  "runHistory.status.failed": "失败",

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
  "projectCard.noScans": "暂无扫描",

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
  "chat.discussProject": "讨论这个项目",
  "chat.currentProject": "当前项目",
  "chat.selectProject": "选择项目",
  "chat.allProjects": "不限定项目",
  "chat.noProjectSelected": "未选择项目",
  "chat.projectHint": "聊天会使用所选项目已保存的监控摘要，不会自动读取当前页面上临时显示的状态。",
  "chat.contextLoaded": "项目分析就绪",
  "chat.contextKeywords": "追踪关键词",
  "chat.contextCompetitors": "竞品",
  "chat.contextGaps": "关键词差距",
  "chat.contextFindings": "最近发现",
  "chat.contextQuickStart": "快速开始",

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
  "settings.browserOverrideActive": "浏览器覆盖配置生效",
  "settings.serverDefaultActive": "服务端默认配置生效",

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
  "settings.tavilyOptional": "Tavily 为可选项（回退覆盖会减少）",

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

  // Setup Banner
  "setup.title": "请先配置 API 密钥",
  "setup.description": "OpenCMO 需要 API 密钥来驱动 AI 功能（内容生成、SEO 分析、网络搜索等）。请在设置中配置您自己的密钥。",
  "setup.llmKey": "大模型 API Key（OpenAI / DeepSeek）",
  "setup.tavilyKey": "Tavily 搜索 Key",
  "setup.tavilyOptional": "Tavily 搜索 Key（可选）",
  "setup.configureNow": "前往设置",
  "setup.dismissHint": "本次不再提醒",

  // Settings
  "settings.localKeysHint": "您的 API 密钥仅保存在本地浏览器中，不会上传到服务器。",

  // Dashboard — subtitle
  "dashboard.subtitle": "您的 AI 营销活动概览",

  // Welcome Hero (onboarding)
  "welcome.title": "欢迎使用 OpenCMO",
  "welcome.subtitle": "您的 AI 营销官从这里开始。粘贴一个 URL，即可获得完整的营销审计报告。",
  "welcome.step1": "配置 API 密钥",
  "welcome.step1Done": "API 密钥已配置",
  "welcome.step2": "输入您的网站 URL 开始分析",
  "welcome.featureSeo": "SEO 与性能审计",
  "welcome.featureSeoDesc": "核心 Web 指标、站点健康度和技术 SEO 分析。",
  "welcome.featureGeo": "AI 搜索可见度",
  "welcome.featureGeoDesc": "查看 ChatGPT、Claude、Gemini、Perplexity 如何提及您的品牌。",
  "welcome.featureCommunity": "社区监控",
  "welcome.featureCommunityDesc": "追踪 Reddit、HN、Twitter 等平台的相关讨论。",

  // Reports Page
  "reports.title": "AI CMO 报告",
  "reports.description": "战略报告深入分析项目定位、竞争优势与风险、市场环境变化。周报回顾最近 7 天的监控数据，总结关键变化、影响分析和下周行动计划。",
  "reports.strategic": "战略报告",
  "reports.strategicDesc": "基于项目背景、优劣势、竞品追踪和最新监控数据生成。这是项目当前状态的董事会级视图。",
  "reports.regenerateStrategic": "重新生成战略报告",
  "reports.weekly": "周报",
  "reports.weeklyDesc": "基于最近七天的监控窗口生成。总结最大变化、数据置信度以及下周下游 Agent 的重点工作。",
  "reports.regenerateWeekly": "重新生成周报",
  "reports.humanReadout": "管理层报告",
  "reports.humanReadoutTip": "面向管理层和团队的深度分析报告，包含完整的数据解读和战略建议。",
  "reports.agentBrief": "Agent 简报",
  "reports.agentBriefTip": "面向 AI Agent 的精简行动清单，用于驱动后续自动化任务。",
  "reports.noReport": "尚未生成报告。",
  "reports.failed": "报告生成失败。",
  "reports.lowSample": "样本量低",
  "reports.sendEmail": "发送周报邮件",
  "reports.sending": "发送中...",
  "reports.strategicHistory": "战略报告历史",
  "reports.weeklyHistory": "周报历史",
  "reports.latest": "最新",

  // Approvals Page
  "approvals.title": "内容审批",
  "approvals.subtitle": "在内容发布前，审核确切的发布内容。",
  "approvals.pending": "待审批",
  "approvals.showingPending": "当前显示 {{count}} 条待审批",
  "approvals.empty": "审批队列为空",
  "approvals.emptyDesc": "待审批的内容预览将显示在这里。",
  "approvals.preview": "生成预览",
  "approvals.channel": "渠道",
  "approvals.target": "目标",
  "approvals.targetUrl": "目标 URL",
  "approvals.created": "创建时间",
  "approvals.reject": "拒绝",
  "approvals.approvePublish": "批准并发布",
  "approvals.autopilot": "自动驾驶",
  "approvals.aiReasoning": "AI 推理",
  "approvals.autoPublishDisabled": "自动发布未启用",
  "approvals.autoPublishHint": "要发布内容到外部平台（Reddit、Twitter 等），需要在设置中开启 OPENCMO_AUTO_PUBLISH。",
  "approvals.goToSettings": "前往设置",

  // Community Page — extra labels
  "community.latestHits": "最新命中",
  "community.avgEngagement": "平均互动度",
  "community.platforms": "平台数",
  "community.platformBreakdown": "平台分布",
  "community.directMentions": "直接提及",
  "community.directMentionsDesc": "标题、正文或评论里明确提到品牌、产品或清晰品牌信号的结果。",
  "community.opportunityThreads": "机会话题",
  "community.opportunityThreadsDesc": "没有直接提到品牌，但与问题、品类或竞品高度相关，适合参与。",
  "community.confidence": "置信度",
  "community.intent.direct_mention": "直接提及",
  "community.intent.competitor_mention": "竞品语境",
  "community.intent.opportunity": "机会话题",
  "community.source.post": "帖子",
  "community.source.comment": "评论",
  "community.source.externalSearch": "外部搜索",
  "community.externalSearchNoMetrics": "外部搜索结果，不含原生互动指标",
  "community.source.unknown": "未知来源",

  // SERP Page — extra labels
  "serp.avgPosition": "平均排名",
  "serp.inTop3": "Top 3",
  "serp.inTop10": "Top 10",
  "serp.positionDistribution": "排名分布",

  // GEO Page — extra labels
  "geo.geoScore": "GEO 评分",
  "geo.visibility": "可见度",
  "geo.position": "位置",
  "geo.sentiment": "情感",
  "geo.sentimentUnavailable": "最新 GEO 扫描未拿到情感分，这次总分不包含该项。",
  "geo.latestSnapshot": "最新快照",

  // Action Tips
  "actionTip.seoExcellent": "SEO 性能优秀，继续保持！",
  "actionTip.seoPoor": "网站性能严重偏低，建议优先优化 LCP 和 TBT。",
  "actionTip.seoWarning": "性能有待提升，考虑优化图片和减少 JavaScript 体积。",
  "actionTip.lcpSlow": "LCP 偏高（>4s），可能影响 Google 排名。",
  "actionTip.clsHigh": "布局偏移过大，建议为图片和广告设置固定尺寸。",
  "actionTip.geoExcellent": "AI 搜索可见度良好！",
  "actionTip.geoPoor": "AI 搜索引擎几乎看不到您的品牌，查看报告获取改进建议。",
  "actionTip.geoWarning": "AI 可见度偏低，可考虑在各平台建立品牌内容。",
  "actionTip.serpNoKeywords": "还没有跟踪任何关键词，添加关键词来监控搜索排名。",
  "actionTip.serpPoor": "大多数关键词排名靠后，查看报告获取 SEO 策略建议。",
  "actionTip.serpGood": "{{count}} 个关键词进入 Top 3！🎉",
  "actionTip.communityNone": "暂未发现社区讨论。AI 对话可以帮您制定社区推广策略。",
  "actionTip.communityActive": "发现活跃社区讨论！可使用审批队列回复关键帖子。",

  // Delete confirmation
  "dashboard.deleteConfirm": "确定要删除该项目吗？",

  // Brand Kit Page
  "brandKit.title": "品牌套件",
  "brandKit.subtitle": "定义品牌 DNA。每个 AI 代理生成内容时都将遵循这些准则。",
  "brandKit.backToDashboard": "返回仪表盘",
  "brandKit.backToProject": "返回项目总览",
  "brandKit.saving": "保存中...",
  "brandKit.saved": "已保存",
  "brandKit.toneLabel": "品牌语调",
  "brandKit.tonePlaceholder": "例如：专业但亲切，技术自信，善用生活类比...",
  "brandKit.toneDesc": "描述所有 AI 生成内容应保持一致的品牌个性和表达风格。",
  "brandKit.audienceLabel": "目标受众",
  "brandKit.audiencePlaceholder": "例如：25-45 岁、精通技术的独立开发者和 B2B SaaS 创始人...",
  "brandKit.audienceDesc": "您为谁创建内容？尽可能具体。",
  "brandKit.valuesLabel": "核心价值主张",
  "brandKit.valuesPlaceholder": "例如：开源、隐私优先的分析工具 — 数据永不离开用户服务器...",
  "brandKit.valuesDesc": "您的产品独特之处是什么？每条内容应强化的核心信息是什么？",
  "brandKit.forbiddenLabel": "禁用词汇与短语",
  "brandKit.forbiddenDesc": "品牌在任何内容中都不该使用的词汇（敏感词、竞品名称等）。",
  "brandKit.examplesLabel": "最佳内容示例",
  "brandKit.examplesPlaceholder": "粘贴您表现最好的推文、Reddit 帖子或博客摘要...",
  "brandKit.examplesDesc": "提供 1-3 个完美体现品牌语调的内容示例。",
  "brandKit.instructionsLabel": "自定义指令",
  "brandKit.instructionsPlaceholder": "例如：始终提及开源特性，不要直接与 X 竞品比较...",
  "brandKit.instructionsDesc": "代理生成内容时应遵循的其他规则或上下文。",
  "brandKit.tagPlaceholder": "输入后按回车添加...",
  "brandKit.tagMore": "继续添加...",

  // Performance Page
  "perf.title": "效果追踪器",
  "perf.subtitle": "追踪已发布内容和手动添加链接的互动指标。",
  "perf.trackUrl": "追踪 URL",
  "perf.totalPublished": "总发布数",
  "perf.totalLikes": "总点赞数",
  "perf.totalComments": "总评论数",
  "perf.totalShares": "总分享数",
  "perf.trackExternal": "追踪外部 URL",
  "perf.titleOptional": "标题（可选）",
  "perf.notesOptional": "备注（可选）",
  "perf.adding": "添加中...",
  "perf.add": "添加",
  "perf.publishedVia": "通过审批队列发布",
  "perf.manuallyTracked": "手动追踪",
  "perf.untitled": "无标题",
  "perf.refreshMetrics": "刷新指标",
  "perf.emptyTitle": "暂无追踪内容",
  "perf.emptyDesc": "通过审批队列发布的内容将自动显示在此处。您也可以手动添加外部 URL 进行追踪。",
  "perf.platformReddit": "Reddit",
  "perf.platformTwitter": "Twitter/X",
  "perf.platformBlog": "博客",
  "perf.platformOther": "其他",

  // Task Progress (scan)
  "taskProgress.scanInProgress": "扫描进行中…",
  "taskProgress.scanComplete": "扫描完成",
  "taskProgress.scanErrors": "扫描完成但有错误",
  "taskProgress.initializing": "正在初始化扫描…",
  "taskProgress.findings": "个发现",
  "taskProgress.actions": "个行动",
  "taskProgress.stageContextBuild": "上下文分析",
  "taskProgress.stageSignalCollect": "信号采集",
  "taskProgress.stageSignalNormalize": "信号处理",
  "taskProgress.stageDomainReview": "领域审查",
  "taskProgress.stageStrategySynthesis": "策略汇总",
  "taskProgress.stagePersistPublish": "保存结果",
  "taskProgress.stageReporting": "报告生成",

  // Pipeline Progress (report generation)
  "pipeline.connecting": "正在连接流水线...",
  "pipeline.preparing": "正在准备流水线...",
  "pipeline.agentsWorking": "AI 代理正在工作中...",
  "pipeline.complete": "报告生成完成！",
  "pipeline.error": "流水线遇到错误",
  "pipeline.phaseReflection": "阶段 1 · 数据质量审计",
  "pipeline.phaseDistillation": "阶段 2 · 洞察提炼",
  "pipeline.phasePlanning": "阶段 3 · 大纲规划",
  "pipeline.phaseWriting": "阶段 4 · 章节撰写",
  "pipeline.phaseGrading": "阶段 5 · 质量评分",
  "pipeline.phaseSynthesis": "阶段 6 · 最终合成",

  // Action Feed
  "actionFeed.title": "行动反馈",
  "actionFeed.allClear": "一切正常！🎉",
  "actionFeed.allClearDesc": "当前没有紧急操作。代理正在监控，有需要注意的事项时会提醒您。",
  "actionFeed.viewDetails": "查看详情",
  "actionFeed.reviewDraft": "审阅草稿",
  "actionFeed.generateFix": "生成修复",
  "actionFeed.discuss": "讨论",

  // Competitor Panel
  "competitor.title": "竞品管理",
  "competitor.aiDiscover": "AI 智能发现",
  "competitor.discovering": "AI 分析中...",
  "competitor.manual": "手动添加",
  "competitor.manualAdd": "手动添加",
  "competitor.aiDiscoverSuccess": "AI 发现了 {{count}} 个竞品，已自动添加到图谱",
  "competitor.aiDiscoverFailed": "AI 发现失败，请检查 API 配置后重试",
  "competitor.namePlaceholder": "竞品名称 *",
  "competitor.urlPlaceholder": "网址（可选）",
  "competitor.kwPlaceholder": "关键词，逗号分隔（可选）",
  "competitor.adding": "添加中...",
  "competitor.noCompetitorsAi": "暂无竞品。点击「AI 智能发现」让 AI 自动分析并添加竞品。",

  // Analysis Dialog
  "analysis.title": "AI 监控编排",
  "analysis.initializing": "正在初始化监控工作流...",
  "analysis.workflowStages": "阶段进度",
  "analysis.domainReviews": "领域结论",
  "analysis.keyFindings": "主要发现",
  "analysis.recommendedActions": "行动建议",
  "analysis.workflowFailed": "流程失败",
  "analysis.workflowComplete": "流程完成",
  "analysis.stages": "阶段",
  "analysis.close": "关闭",
  "analysis.runBackground": "后台运行",
  "analysis.backgroundHint": "分析在后台运行，可以随时关闭此窗口。",
  "analysis.closeBackground": "关闭并继续后台运行",
  "analysis.stageContextBuild": "上下文构建",
  "analysis.stageSignalCollect": "信号采集",
  "analysis.stageSignalNormalize": "证据归一化",
  "analysis.stageDomainReview": "领域研判",
  "analysis.stageStrategySynthesis": "策略汇总",
  "analysis.stagePersistPublish": "结果落库",

  // Project Header
  "projectHeader.resume": "恢复运行",
  "projectHeader.pause": "暂停运行",

  // Approval Card extras
  "approval.replyTo": "回复 {{id}}",
  "approval.chars": "{{count}} 个字符",
  "approval.whyThis": "为何选这个：",
  "approval.whyNow": "为何现在：",
  "approval.whyHere": "为何在这里：",

  // Reports extras
  "reports.emailSent": "周报已发送至 {{recipient}}。",
  "reports.downloadPdf": "下载 PDF",

  // Monitor List extras
  "monitorList.deleteMonitor": "删除监控",

  // Chat — context badge (ChatContainer)
  "chat.projectContextBadge": "项目上下文",
  "chat.discussions": "讨论",

  // Chat — project context card
  "chat.community": "社区讨论",
  "chat.communityHitsSuffix": " 条",
  "chat.serpInTop10Suffix": " 进前10",
  "chat.gapNote": "（竞品有，你没有）",
  "chat.aiGreeting": "我已了解 {{name}} 的最新监控数据。你可以让我生成任意平台的营销内容、分析竞品、或制定推广策略。",
  "chat.suggestStrategy": "全渠道营销方案",
  "chat.suggestStrategyPrompt": "针对 {{name}} 项目，制定一个全平台推广方案",
  "chat.suggestCompetitor": "竞品深度分析",
  "chat.suggestCompetitorPrompt": "深度分析 {{name}} 的竞争对手，给出差异化建议",
  "chat.suggestVisibility": "提升 AI 可见度",
  "chat.suggestVisibilityPrompt": "如何提升 {{name}} 在 AI 搜索引擎中的可见度？",
  "chat.suggestBlog": "生成博客文章",
  "chat.suggestBlogPrompt": "针对 {{name}} 项目，帮我写一篇 SEO 博客文章",

  // Agent Grid
  "agentGrid.title": "选择一个 AI 专家开始对话",
  "agentGrid.subtitle": "或直接在下方输入任何问题，CMO 总管会自动分配给合适的专家",
  "agentGrid.projectPrefix": "针对 {{name}} 项目，",
  "agentGrid.cmoPrompt": "帮我分析 {{name}} 项目的整体营销策略和当前状况",

  // Monitors Page — analysis bar
  "monitors.aiAnalyzing": "AI 正在分析",
  "monitors.viewDetails": "查看详情",

  // Knowledge Graph — type labels
  "graph.type.brand": "品牌",
  "graph.type.keyword": "关键词",
  "graph.type.discussion": "社区讨论",
  "graph.type.serp": "搜索排名",
  "graph.type.competitor": "竞品",
  "graph.type.competitorKeyword": "竞品关键词",

  // Knowledge Graph — node details
  "graph.platform": "平台",
  "graph.engagement": "互动分",
  "graph.nodeComments": "评论数",
  "graph.rank": "排名",
  "graph.discoveryDepth": "发现深度",
  "graph.openLink": "访问链接",
  "graph.controlsHint": "拖拽旋转 · 滚轮缩放 · 右键平移 · 点击节点打开链接",

  // Cron human-readable descriptions
  "cron.everyHour": "每小时",
  "cron.everyMinute": "每分钟",
  "cron.everyNHours": "每 {{n}} 小时",
  "cron.dailyAt": "每天 {{time}}",
  "cron.weeklyAt": "每周{{day}} {{time}}",
  "cron.monthlyAt": "每月 {{day}} 日 {{time}}",
  "cron.day.0": "日",
  "cron.day.1": "一",
  "cron.day.2": "二",
  "cron.day.3": "三",
  "cron.day.4": "四",
  "cron.day.5": "五",
  "cron.day.6": "六",
};

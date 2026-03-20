export const en = {
  // Common
  "common.cancel": "Cancel",
  "common.confirm": "Confirm",
  "common.logout": "Logout",
  "common.noData": "No data",
  "common.error": "Error",
  "common.never": "Never",
  "common.projectNotFound": "Project not found",

  // Nav / Sidebar
  "nav.dashboard": "Dashboard",
  "nav.monitors": "Monitors",
  "nav.aiChat": "AI Chat",
  "nav.projects": "Projects",

  // Auth
  "auth.enterToken": "Enter your access token to continue.",
  "auth.tokenPlaceholder": "Token",
  "auth.loggingIn": "Logging in...",
  "auth.login": "Login",
  "auth.invalidToken": "Invalid token",

  // Dashboard
  "dashboard.title": "Dashboard",
  "dashboard.newMonitor": "New Monitor",
  "dashboard.noProjects": "No projects yet",
  "dashboard.noProjectsDesc": "Add a website URL to start monitoring your brand's online presence.",
  "dashboard.createMonitor": "Add Website",

  // Project Tabs
  "project.overview": "Overview",
  "project.seo": "SEO",
  "project.geo": "GEO",
  "project.serp": "SERP",
  "project.community": "Community",

  // Score Panel
  "score.seoScore": "SEO Score",
  "score.geoScore": "GEO Score",
  "score.communityHits": "Community Hits",
  "score.serpKeywords": "SERP Keywords",
  "score.tracked": "{{count}} tracked",

  // Scan History
  "scan.latestScans": "Latest Scans",
  "scan.type": "Type",
  "scan.lastScanned": "Last Scanned",
  "scan.result": "Result",
  "scan.hits": "{{count}} hits",

  // SEO Page
  "seo.noData": "No SEO data yet",
  "seo.noDataDesc": "Run a scan to see SEO metrics.",
  "seo.performanceScore": "Performance Score",
  "seo.coreWebVitals": "Core Web Vitals",

  // GEO Page
  "geo.noData": "No GEO data yet",
  "geo.noDataDesc": "Run a scan to see AI visibility metrics.",
  "geo.scoreTrend": "GEO Score Trend",

  // SERP Page
  "serp.trackedKeywords": "Tracked Keywords",
  "serp.rankingHistory": "Ranking History",

  // Community Page
  "community.scanHistory": "Scan History",
  "community.trackedDiscussions": "Tracked Discussions",
  "community.noDiscussions": "No discussions found",
  "community.noDiscussionsDesc": "Run a community scan to discover discussions.",
  "community.comments": "{{count}} comments",
  "community.engagement": "engagement: {{score}}",

  // Monitors Page
  "monitors.title": "Monitors",
  "monitors.newMonitor": "New Monitor",
  "monitors.noMonitors": "No monitors yet",
  "monitors.noMonitorsDesc": "Enter a website URL above to start monitoring.",

  // Monitor Form
  "monitorForm.urlPlaceholder": "https://your-website.com",
  "monitorForm.subtitle": "AI will automatically analyze your brand, SEO, community visibility and more.",
  "monitorForm.analyzing": "Analyzing...",
  "monitorForm.startMonitoring": "Start Monitoring",

  // Monitor List
  "monitorList.brand": "Brand",
  "monitorList.type": "Type",
  "monitorList.cron": "Cron",
  "monitorList.lastRun": "Last Run",
  "monitorList.actions": "Actions",
  "monitorList.schedule": "Schedule",
  "monitorList.fullScan": "Full scan",

  // Run Scan
  "runScan.running": "Running...",
  "runScan.done": "Done",
  "runScan.failed": "Failed",
  "runScan.run": "Run",

  // Keywords
  "keywords.addPlaceholder": "Add keyword...",
  "keywords.add": "Add",
  "keywords.noKeywords": "No keywords tracked yet.",
  "keywords.keyword": "Keyword",
  "keywords.position": "Position",
  "keywords.lastChecked": "Last Checked",

  // Project Card
  "projectCard.hits": "{{count}} hits",
  "projectCard.kw": "{{count}} kw",

  // Chat
  "chat.title": "AI Chat",
  "chat.agent": "Agent: {{name}}",
  "chat.newChat": "New Chat",
  "chat.placeholder": "Type a message...",
  "chat.emptyState": "Ask anything about your marketing strategy...",
  "chat.thinking": "Thinking...",
  "chat.today": "Today",
  "chat.yesterday": "Yesterday",
  "chat.older": "Older",
  "chat.noHistory": "No conversations yet",

  // Settings
  "settings.title": "Settings",
  "settings.apiKey": "API Key",
  "settings.apiKeyPlaceholder": "sk-...",
  "settings.apiKeyHint": "Your OpenAI-compatible API key. Stored on the server.",
  "settings.baseUrl": "Base URL (optional)",
  "settings.baseUrlPlaceholder": "https://api.openai.com/v1",
  "settings.baseUrlHint": "For custom providers like DeepSeek, NVIDIA, Ollama, etc.",
  "settings.model": "Model (optional)",
  "settings.modelPlaceholder": "gpt-4o",
  "settings.modelHint": "Override the default model.",
  "settings.save": "Save",
  "settings.saved": "Saved!",
  "settings.apiKeySet": "API key is configured",
  "settings.apiKeyNotSet": "No API key configured",
} as const;

export type TranslationKey = keyof typeof en;

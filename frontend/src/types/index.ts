export interface Project {
  id: number;
  brand_name: string;
  url: string;
  category: string;
  latest?: LatestScans;
}

export interface LatestScans {
  seo: { scanned_at: string; score: number | null } | null;
  geo: { scanned_at: string; score: number } | null;
  community: { scanned_at: string; total_hits: number } | null;
  serp: SerpSnapshot[];
}

export interface SerpSnapshot {
  keyword: string;
  position: number | null;
  url_found?: string | null;
  provider?: string;
  error?: string | null;
  checked_at?: string;
}

export interface Monitor {
  id: number;
  project_id: number;
  brand_name: string;
  url: string;
  category: string;
  job_type: string;
  cron_expr: string;
  enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
}

export interface MonitorRun {
  id: number;
  task_id: string;
  job_type: string;
  status: "pending" | "running" | "completed" | "failed";
  summary: string | null;
  created_at: string;
  completed_at: string | null;
  findings_count: number;
  recommendations_count: number;
}

export interface TaskRecord {
  task_id: string;
  monitor_id: number;
  project_id: number;
  job_type: string;
  status: "pending" | "running" | "completed" | "failed";
  created_at: string;
  completed_at: string | null;
  error: string | null;
  progress: AnalysisProgress[];
  run_id?: number | null;
  summary?: string;
  findings_count?: number;
  recommendations_count?: number;
}

export type ApprovalStatus = "pending" | "approved" | "rejected" | "failed";

export interface ApprovalRecord {
  id: number;
  project_id: number;
  channel: string;
  approval_type: string;
  status: ApprovalStatus;
  title: string;
  target_label: string;
  target_url: string;
  agent_name: string;
  content: string;
  payload: Record<string, unknown>;
  preview: Record<string, unknown>;
  publish_result: Record<string, unknown> | null;
  decision_note: string;
  created_at: string;
  decided_at: string | null;
  source_insight_id?: number | null;
  pre_metrics_json?: string;
  post_metrics_json?: string;
}

export interface AnalysisProgress {
  role?: string;
  content?: string;
  round?: number;
  stage?: string;
  status?: "started" | "running" | "completed" | "failed";
  agent?: string;
  summary?: string;
  detail?: string;
}

export interface Finding {
  domain: string;
  severity: "critical" | "warning" | "info";
  title: string;
  summary: string;
  confidence: number | null;
  evidence_refs: Array<{
    domain: string;
    source: string;
    key: string;
    value: string;
    url?: string | null;
  }>;
}

export interface Recommendation {
  domain: string;
  priority: "high" | "medium" | "low";
  owner_type: string;
  action_type: string;
  title: string;
  summary: string;
  rationale: string;
  confidence: number | null;
  evidence_refs: Array<{
    domain: string;
    source: string;
    key: string;
    value: string;
    url?: string | null;
  }>;
}

export interface MonitoringSummary {
  run_id: number;
  status: "pending" | "running" | "completed" | "failed";
  summary: string;
  created_at: string;
  completed_at: string | null;
  findings_count: number;
  recommendations_count: number;
}

export interface SeoScan {
  id: number;
  url: string;
  scanned_at: string;
  score_performance: number | null;
  score_lcp: number | null;
  score_cls: number | null;
  score_tbt: number | null;
  has_robots_txt: boolean | null;
  has_sitemap: boolean | null;
  has_schema_org: boolean | null;
}

export interface GeoScan {
  id: number;
  scanned_at: string;
  geo_score: number;
  visibility_score: number | null;
  position_score: number | null;
  sentiment_score: number | null;
  platform_results_json: string;
}

export interface CommunityScan {
  id: number;
  scanned_at: string;
  total_hits: number;
  results_json: string;
}

export interface Discussion {
  id: number;
  platform: string;
  detail_id: string;
  title: string;
  url: string;
  first_seen_at: string;
  last_checked_at: string;
  raw_score: number | null;
  comments_count: number | null;
  engagement_score: number | null;
}

export interface TrackedKeyword {
  id: number;
  keyword: string;
  created_at: string;
}

export interface ChartData {
  labels: string[];
  [key: string]: (number | null)[] | string[];
}

export interface SerpChartData {
  labels: string[];
  keywords: string[];
  positions: Record<string, (number | null)[]>;
}

export interface CommunityChartData {
  scan_labels: string[];
  scan_hits: number[];
  platform_labels: string[];
  platform_counts: number[];
}

export interface ChatEvent {
  type:
    | "delta"
    | "agent"
    | "tool_call"
    | "tool_done"
    | "handoff"
    | "handoff_done"
    | "tool_search"
    | "tool_search_done"
    | "message_created"
    | "reasoning"
    | "done"
    | "error";
  content?: string;
  name?: string;
  target?: string;
  agent_name?: string;
  final_output?: string;
  message?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  tools?: ToolStatus[];
}

export interface ToolStatus {
  name: string;
  done: boolean;
}

export interface ProjectSummary {
  project: Project;
  latest: LatestScans;
  previous: {
    seo?: { scanned_at: string; score: number | null };
    geo?: { scanned_at: string; score: number };
  } | null;
  latest_monitoring?: MonitoringSummary | null;
}

export interface ChatSessionSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  project_id: number | null;
  project_name?: string | null;
}

export interface AISettings {
  api_key_set: boolean;
  api_key_masked: string;
  base_url: string;
  model: string;
  // Reddit
  reddit_configured: boolean;
  reddit_username: string;
  auto_publish: boolean;
  // Twitter
  twitter_configured: boolean;
  twitter_api_key_masked: string;
  // GEO
  anthropic_key_set: boolean;
  anthropic_key_masked: string;
  google_ai_key_set: boolean;
  google_ai_key_masked: string;
  geo_chatgpt_enabled: boolean;
  // SEO
  pagespeed_key_set: boolean;
  pagespeed_key_masked: string;
  // Search (Tavily)
  tavily_key_set: boolean;
  tavily_key_masked: string;
  // SERP
  dataforseo_configured: boolean;
  dataforseo_login: string;
  // Email
  email_configured: boolean;
  smtp_host: string;
  smtp_port: string;
  smtp_user: string;
  report_email: string;
}

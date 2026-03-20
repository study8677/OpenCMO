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
}

export interface AnalysisProgress {
  role: string;
  content: string;
  round: number;
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
}

export interface ChatSessionSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface AISettings {
  api_key_set: boolean;
  api_key_masked: string;
  base_url: string;
  model: string;
}

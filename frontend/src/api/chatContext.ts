import { apiJson } from "./client";

export interface ChatContextScores {
  seo: number | null;
  geo: number | null;
  community_hits: number | null;
  serp_tracked: number;
  serp_top10: number;
}

export interface ChatContextFinding {
  domain: string;
  severity: "critical" | "warning" | "info";
  title: string;
}

export interface ChatContextCompetitor {
  label: string;
  url: string;
}

export interface ChatProjectContext {
  project: {
    id: number;
    brand_name: string;
    url: string;
    category: string;
  };
  scores: ChatContextScores;
  keywords: string[];
  competitors: ChatContextCompetitor[];
  keyword_gaps: string[];
  findings: ChatContextFinding[];
}

export function getChatContext(projectId: number): Promise<ChatProjectContext> {
  return apiJson<ChatProjectContext>(`/chat/context/${projectId}`);
}

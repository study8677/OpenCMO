import { apiJson, apiFetch } from "./client";

export interface GraphNode {
  id: string;
  label: string;
  type: "brand" | "keyword" | "discussion" | "serp" | "competitor" | "competitor_keyword";
  url?: string;
  category?: string;
  platform?: string;
  engagement?: number;
  comments?: number;
  position?: number;
  provider?: string;
  depth?: number;
  explored?: boolean;
}

export interface GraphLink {
  source: string;
  target: string;
  type: "has_keyword" | "has_discussion" | "serp_rank" | "competitor_of" | "comp_keyword" | "keyword_overlap" | "expanded_from";
}

export interface ExpansionState {
  desired_state: "idle" | "running" | "paused";
  runtime_state: "idle" | "running" | "paused" | "interrupted";
  current_wave: number;
  nodes_discovered: number;
  nodes_explored: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  expansion?: ExpansionState | null;
}

export interface Competitor {
  id: number;
  name: string;
  url: string | null;
  category: string | null;
  created_at: string;
}

export async function fetchGraph(projectId: number): Promise<GraphData> {
  return apiJson<GraphData>(`/projects/${projectId}/graph`);
}

export async function fetchCompetitors(projectId: number): Promise<Competitor[]> {
  return apiJson<Competitor[]>(`/projects/${projectId}/competitors`);
}

export async function addCompetitor(
  projectId: number,
  data: { name: string; url?: string; category?: string; keywords?: string[] },
): Promise<{ id: number; name: string }> {
  return apiJson(`/projects/${projectId}/competitors`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteCompetitor(competitorId: number): Promise<void> {
  await apiFetch(`/competitors/${competitorId}`, { method: "DELETE" });
}

export async function discoverCompetitors(
  projectId: number,
): Promise<{ competitors: { id: number; name: string; url: string | null; keywords: string[] }[] }> {
  return apiJson(`/projects/${projectId}/discover-competitors`, {
    method: "POST",
  });
}

// --- Expansion API ---

export async function fetchExpansionStatus(projectId: number): Promise<ExpansionState> {
  return apiJson<ExpansionState>(`/projects/${projectId}/expansion`);
}

export async function startExpansion(projectId: number): Promise<{ status: string }> {
  return apiJson(`/projects/${projectId}/expansion/start`, { method: "POST" });
}

export async function pauseExpansion(projectId: number): Promise<{ ok: boolean }> {
  return apiJson(`/projects/${projectId}/expansion/pause`, { method: "POST" });
}

export async function resetExpansion(projectId: number): Promise<{ ok: boolean }> {
  return apiJson(`/projects/${projectId}/expansion/reset`, { method: "POST" });
}

export async function fetchExpansionProgress(projectId: number): Promise<{ progress: Array<{ stage: string; status: string; summary: string }> }> {
  return apiJson(`/projects/${projectId}/expansion/progress`);
}

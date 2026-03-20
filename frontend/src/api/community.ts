import { apiJson } from "./client";
import type { CommunityScan, Discussion, CommunityChartData } from "../types";

export function getCommunityHistory(
  projectId: number,
): Promise<CommunityScan[]> {
  return apiJson<CommunityScan[]>(`/projects/${projectId}/community/history`);
}

export function getDiscussions(projectId: number): Promise<Discussion[]> {
  return apiJson<Discussion[]>(`/projects/${projectId}/community/discussions`);
}

export function getCommunityChart(
  projectId: number,
): Promise<CommunityChartData> {
  return apiJson<CommunityChartData>(`/projects/${projectId}/community/chart`);
}

import { apiJson } from "./client";
import type { SerpSnapshot, SerpChartData } from "../types";

export function getSerpLatest(projectId: number): Promise<SerpSnapshot[]> {
  return apiJson<SerpSnapshot[]>(`/projects/${projectId}/serp/latest`);
}

export function getSerpChart(projectId: number): Promise<SerpChartData> {
  return apiJson<SerpChartData>(`/projects/${projectId}/serp/chart`);
}

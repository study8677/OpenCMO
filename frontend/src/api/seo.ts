import { apiJson } from "./client";
import type { SeoScan, ChartData } from "../types";

export function getSeoHistory(projectId: number): Promise<SeoScan[]> {
  return apiJson<SeoScan[]>(`/projects/${projectId}/seo/history`);
}

export function getSeoChart(projectId: number): Promise<ChartData> {
  return apiJson<ChartData>(`/projects/${projectId}/seo/chart`);
}

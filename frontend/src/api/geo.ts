import { apiJson } from "./client";
import type { GeoScan, ChartData } from "../types";

export function getGeoHistory(projectId: number): Promise<GeoScan[]> {
  return apiJson<GeoScan[]>(`/projects/${projectId}/geo/history`);
}

export function getGeoChart(projectId: number): Promise<ChartData> {
  return apiJson<ChartData>(`/projects/${projectId}/geo/chart`);
}

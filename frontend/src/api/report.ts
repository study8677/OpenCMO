import { apiJson } from "./client";
import type { LatestReports, ReportBundle, ReportKind, ReportRecord } from "../types";

export function sendReport(
  projectId: number,
): Promise<{ ok: boolean; recipient?: string; report_id?: number; error?: string }> {
  return apiJson(`/projects/${projectId}/report`, { method: "POST" });
}

export function listReports(projectId: number): Promise<ReportRecord[]> {
  return apiJson<ReportRecord[]>(`/projects/${projectId}/reports`);
}

export function getLatestReports(projectId: number): Promise<LatestReports> {
  return apiJson<LatestReports>(`/projects/${projectId}/reports/latest`);
}

export function regenerateReport(projectId: number, kind: ReportKind): Promise<ReportBundle> {
  return apiJson<ReportBundle>(`/projects/${projectId}/reports/${kind}/regenerate`, {
    method: "POST",
  });
}

import { apiJson } from "./client";

export interface PerformanceItem {
  id: number;
  channel: string;
  approval_type: string;
  title: string;
  content_preview: string;
  publish_result: Record<string, unknown> | null;
  pre_metrics: Record<string, number>;
  post_metrics: Record<string, number>;
  created_at: string;
  decided_at: string;
}

export interface ManualTrackingItem {
  id: number;
  platform: string;
  url: string;
  title: string;
  notes: string;
  metrics: Record<string, number>;
  created_at: string;
}

export interface PerformanceSummary {
  total_published: number;
  total_likes: number;
  total_comments: number;
  total_retweets: number;
}

export interface PerformanceData {
  summary: PerformanceSummary;
  approvals: PerformanceItem[];
  manual: ManualTrackingItem[];
}

export function getPerformance(projectId: number): Promise<PerformanceData> {
  return apiJson<PerformanceData>(`/projects/${projectId}/performance`);
}

export function refreshMetrics(approvalId: number): Promise<{ ok: boolean; metrics?: Record<string, number> }> {
  return apiJson(`/approvals/${approvalId}/refresh-metrics`, { method: "POST" });
}

export function addManualTracking(
  projectId: number,
  data: { platform: string; url: string; title?: string; notes?: string },
): Promise<{ ok: boolean; id: number }> {
  return apiJson(`/projects/${projectId}/manual-tracking`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteManualTracking(trackingId: number): Promise<{ ok: boolean }> {
  return apiJson(`/manual-tracking/${trackingId}`, { method: "DELETE" });
}

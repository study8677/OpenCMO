import { apiJson } from "./client";

export function sendReport(
  projectId: number,
): Promise<{ ok: boolean; recipient?: string; error?: string }> {
  return apiJson(`/projects/${projectId}/report`, { method: "POST" });
}

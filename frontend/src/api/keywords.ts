import { apiJson } from "./client";
import type { TrackedKeyword } from "../types";

export function listKeywords(projectId: number): Promise<TrackedKeyword[]> {
  return apiJson<TrackedKeyword[]>(`/projects/${projectId}/keywords`);
}

export function addKeyword(
  projectId: number,
  keyword: string,
): Promise<{ id: number; keyword: string }> {
  return apiJson(`/projects/${projectId}/keywords`, {
    method: "POST",
    body: JSON.stringify({ keyword }),
  });
}

export function deleteKeyword(keywordId: number): Promise<{ ok: boolean }> {
  return apiJson(`/keywords/${keywordId}`, { method: "DELETE" });
}

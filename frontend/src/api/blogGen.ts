import { apiJson } from "./client";
import type { BlogDraft, BlogStyle } from "../types";

export interface BlogGenerateParams {
  style: BlogStyle;
  bilingual: boolean;
}

export interface BlogGenerateResult {
  task_id: string;
  project_id: number;
  style: string;
  status: string;
}

export function generateBlog(
  projectId: number,
  params: BlogGenerateParams,
): Promise<BlogGenerateResult> {
  return apiJson<BlogGenerateResult>(`/projects/${projectId}/blog/generate`, {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function listBlogDrafts(projectId: number): Promise<BlogDraft[]> {
  return apiJson<BlogDraft[]>(`/projects/${projectId}/blog/drafts`);
}

export function getBlogDraft(draftId: number): Promise<BlogDraft> {
  return apiJson<BlogDraft>(`/blog/drafts/${draftId}`);
}

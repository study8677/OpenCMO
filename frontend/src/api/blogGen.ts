import { apiJson } from "./client";
import type { BlogDraft, BlogStyle, MarketingSkillId } from "../types";

export interface BlogGenerateParams {
  style: BlogStyle;
  skill_id: MarketingSkillId;
  bilingual: boolean;
}

export interface BlogGenerateResult {
  task_id: string;
  project_id: number;
  style: string;
  skill_id: MarketingSkillId;
  skill_name: string;
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

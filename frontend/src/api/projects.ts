import { apiJson } from "./client";
import type { Project, ProjectSummary } from "../types";

export function listProjects(): Promise<Project[]> {
  return apiJson<Project[]>("/projects");
}

export function getProject(id: number): Promise<Project> {
  return apiJson<Project>(`/projects/${id}`);
}

export function getProjectSummary(id: number): Promise<ProjectSummary> {
  return apiJson<ProjectSummary>(`/projects/${id}/summary`);
}

export function deleteProject(id: number): Promise<{ ok: boolean }> {
  return apiJson(`/projects/${id}`, { method: "DELETE" });
}

export interface NextAction {
  domain: string;
  priority: "high" | "medium" | "low";
  icon: string;
  title: string;
  description: string;
}

export function getNextActions(id: number): Promise<{ actions: NextAction[] }> {
  return apiJson<{ actions: NextAction[] }>(`/projects/${id}/next-actions`);
}

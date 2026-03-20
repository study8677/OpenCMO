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

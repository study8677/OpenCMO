import { useQuery } from "@tanstack/react-query";
import { getProject, getProjectSummary } from "../api/projects";
import type { ProjectSummary } from "../types";

export function useProject(id: number) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: () => getProject(id),
  });
}

export function useProjectSummary(id: number) {
  return useQuery<ProjectSummary>({
    queryKey: ["project-summary", id],
    queryFn: () => getProjectSummary(id),
  });
}

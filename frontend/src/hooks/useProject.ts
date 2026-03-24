import { useQuery } from "@tanstack/react-query";
import { getProject, getProjectSummary, getNextActions } from "../api/projects";
import type { NextAction } from "../api/projects";
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

export function useNextActions(id: number) {
  return useQuery<{ actions: NextAction[] }>({
    queryKey: ["next-actions", id],
    queryFn: () => getNextActions(id),
    refetchInterval: 60_000,
  });
}

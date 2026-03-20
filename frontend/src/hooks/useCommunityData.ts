import { useQuery } from "@tanstack/react-query";
import { getCommunityHistory, getDiscussions, getCommunityChart } from "../api/community";

export function useCommunityHistory(projectId: number) {
  return useQuery({
    queryKey: ["community-history", projectId],
    queryFn: () => getCommunityHistory(projectId),
  });
}

export function useDiscussions(projectId: number) {
  return useQuery({
    queryKey: ["discussions", projectId],
    queryFn: () => getDiscussions(projectId),
  });
}

export function useCommunityChart(projectId: number) {
  return useQuery({
    queryKey: ["community-chart", projectId],
    queryFn: () => getCommunityChart(projectId),
  });
}

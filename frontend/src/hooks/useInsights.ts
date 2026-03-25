import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getInsights, getInsightsSummary, markInsightRead } from "../api/insights";

export function useInsightsSummary(projectId?: number) {
  return useQuery({
    queryKey: ["insights-summary", projectId ?? null],
    queryFn: () => getInsightsSummary(projectId),
    refetchInterval: 30_000,
  });
}

export function useInsights(projectId?: number, unread = false) {
  return useQuery({
    queryKey: ["insights", projectId ?? null, unread],
    queryFn: () => getInsights(projectId, unread),
  });
}

export function useMarkInsightRead() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => markInsightRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["insights-summary"] });
      qc.invalidateQueries({ queryKey: ["insights"] });
    },
  });
}

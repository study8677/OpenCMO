import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getPerformance, refreshMetrics, addManualTracking, deleteManualTracking } from "../api/performance";

export function usePerformance(projectId: number) {
  return useQuery({
    queryKey: ["performance", projectId],
    queryFn: () => getPerformance(projectId),
  });
}

export function useRefreshMetrics() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (approvalId: number) => refreshMetrics(approvalId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["performance"] });
    },
  });
}

export function useAddManualTracking(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { platform: string; url: string; title?: string; notes?: string }) =>
      addManualTracking(projectId, data),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["performance", projectId] });
    },
  });
}

export function useDeleteManualTracking(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (trackingId: number) => deleteManualTracking(trackingId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["performance", projectId] });
    },
  });
}

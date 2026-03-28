import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getLatestReports, listReports, regenerateReport, sendReport } from "../api/report";
import type { ReportKind } from "../types";

export function useLatestReports(projectId: number) {
  return useQuery({
    queryKey: ["latest-reports", projectId],
    queryFn: () => getLatestReports(projectId),
  });
}

export function useReports(projectId: number) {
  return useQuery({
    queryKey: ["reports", projectId],
    queryFn: () => listReports(projectId),
  });
}

export function useRegenerateReport(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (kind: ReportKind) => regenerateReport(projectId, kind),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["reports", projectId] }),
        qc.invalidateQueries({ queryKey: ["latest-reports", projectId] }),
        qc.invalidateQueries({ queryKey: ["project-summary", projectId] }),
      ]);
    },
  });
}

export function useSendReport(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => sendReport(projectId),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["reports", projectId] }),
        qc.invalidateQueries({ queryKey: ["latest-reports", projectId] }),
      ]);
    },
  });
}

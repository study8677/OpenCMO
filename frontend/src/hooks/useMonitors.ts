import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listMonitors,
  createMonitor,
  deleteMonitor,
  getMonitorRuns,
  runMonitor,
  updateMonitor,
} from "../api/monitors";

export function useMonitors() {
  return useQuery({
    queryKey: ["monitors"],
    queryFn: listMonitors,
  });
}

export function useCreateMonitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createMonitor,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["monitors"] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateMonitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: number; cron_expr?: string; enabled?: boolean }) =>
      updateMonitor(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["monitors"] }),
  });
}

export function useDeleteMonitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteMonitor,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["monitors"] });
    },
  });
}

export function useRunMonitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, locale }: { id: number; locale?: string }) => runMonitor(id, locale),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["monitors"] });
      qc.invalidateQueries({ queryKey: ["monitor-runs", variables.id] });
    },
  });
}

export function useMonitorRuns(monitorId: number) {
  return useQuery({
    queryKey: ["monitor-runs", monitorId],
    queryFn: () => getMonitorRuns(monitorId),
    enabled: monitorId > 0,
    refetchInterval: 10000,
  });
}

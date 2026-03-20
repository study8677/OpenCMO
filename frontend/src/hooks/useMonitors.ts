import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listMonitors, createMonitor, deleteMonitor, runMonitor } from "../api/monitors";

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
  return useMutation({ mutationFn: runMonitor });
}

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchGraph, fetchCompetitors, addCompetitor, deleteCompetitor, discoverCompetitors,
  fetchExpansionStatus, startExpansion, pauseExpansion, resetExpansion,
} from "../api/graph";
import type { GraphData, Competitor, ExpansionState } from "../api/graph";

export function useGraphData(projectId: number, expansionRunning = false) {
  return useQuery<GraphData>({
    queryKey: ["graph", projectId],
    queryFn: () => fetchGraph(projectId),
    refetchInterval: expansionRunning ? 5_000 : 30_000,
  });
}

export function useExpansionStatus(projectId: number) {
  return useQuery<ExpansionState>({
    queryKey: ["expansion", projectId],
    queryFn: () => fetchExpansionStatus(projectId),
    refetchInterval: (query) => {
      const state = query.state.data?.runtime_state;
      if (state === "running") return 2_000;
      return 10_000;
    },
  });
}

export function useStartExpansion(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => startExpansion(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["expansion", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

export function usePauseExpansion(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => pauseExpansion(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["expansion", projectId] });
    },
  });
}

export function useResetExpansion(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => resetExpansion(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["expansion", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

export function useCompetitors(projectId: number) {
  return useQuery<Competitor[]>({
    queryKey: ["competitors", projectId],
    queryFn: () => fetchCompetitors(projectId),
  });
}

export function useAddCompetitor(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; url?: string; category?: string; keywords?: string[] }) =>
      addCompetitor(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["competitors", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

export function useDeleteCompetitor(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (competitorId: number) => deleteCompetitor(competitorId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["competitors", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

export function useDiscoverCompetitors(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => discoverCompetitors(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["competitors", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

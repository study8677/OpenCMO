import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listKeywords, addKeyword, deleteKeyword } from "../api/keywords";

export function useKeywords(projectId: number) {
  return useQuery({
    queryKey: ["keywords", projectId],
    queryFn: () => listKeywords(projectId),
  });
}

export function useAddKeyword(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (keyword: string) => addKeyword(projectId, keyword),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["keywords", projectId] });
      qc.invalidateQueries({ queryKey: ["serp-latest", projectId] });
    },
  });
}

export function useDeleteKeyword(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteKeyword,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["keywords", projectId] });
    },
  });
}

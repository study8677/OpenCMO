import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getBrandKit, saveBrandKit } from "../api/brandKit";
import type { BrandKit } from "../api/brandKit";

export function useBrandKit(projectId: number) {
  return useQuery({
    queryKey: ["brand-kit", projectId],
    queryFn: () => getBrandKit(projectId),
  });
}

export function useSaveBrandKit(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (kit: Partial<BrandKit>) => saveBrandKit(projectId, kit),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["brand-kit", projectId] });
    },
  });
}

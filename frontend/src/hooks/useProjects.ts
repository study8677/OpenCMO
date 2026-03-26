import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listProjects, deleteProject } from "../api/projects";

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteProject(id),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["projects"] }),
        qc.invalidateQueries({ queryKey: ["overview"] }),
        qc.invalidateQueries({ queryKey: ["insights-summary"] }),
        qc.invalidateQueries({ queryKey: ["insights"] }),
      ]);
    },
  });
}

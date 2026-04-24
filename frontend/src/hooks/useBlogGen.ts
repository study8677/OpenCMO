import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { generateBlog, listBlogDrafts, type BlogGenerateParams } from "../api/blogGen";

export function useBlogGenerate(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: BlogGenerateParams) => generateBlog(projectId, params),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project-summary", projectId] });
      qc.invalidateQueries({ queryKey: ["blog-drafts", projectId] });
    },
  });
}

export function useBlogDrafts(projectId: number) {
  return useQuery({
    queryKey: ["blog-drafts", projectId],
    queryFn: () => listBlogDrafts(projectId),
  });
}

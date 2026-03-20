import { useQuery } from "@tanstack/react-query";
import { getSeoHistory, getSeoChart } from "../api/seo";

export function useSeoHistory(projectId: number) {
  return useQuery({
    queryKey: ["seo-history", projectId],
    queryFn: () => getSeoHistory(projectId),
  });
}

export function useSeoChart(projectId: number) {
  return useQuery({
    queryKey: ["seo-chart", projectId],
    queryFn: () => getSeoChart(projectId),
  });
}

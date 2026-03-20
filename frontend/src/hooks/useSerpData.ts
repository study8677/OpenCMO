import { useQuery } from "@tanstack/react-query";
import { getSerpLatest, getSerpChart } from "../api/serp";

export function useSerpLatest(projectId: number) {
  return useQuery({
    queryKey: ["serp-latest", projectId],
    queryFn: () => getSerpLatest(projectId),
  });
}

export function useSerpChart(projectId: number) {
  return useQuery({
    queryKey: ["serp-chart", projectId],
    queryFn: () => getSerpChart(projectId),
  });
}

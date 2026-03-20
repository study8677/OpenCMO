import { useQuery } from "@tanstack/react-query";
import { getGeoHistory, getGeoChart } from "../api/geo";

export function useGeoHistory(projectId: number) {
  return useQuery({
    queryKey: ["geo-history", projectId],
    queryFn: () => getGeoHistory(projectId),
  });
}

export function useGeoChart(projectId: number) {
  return useQuery({
    queryKey: ["geo-chart", projectId],
    queryFn: () => getGeoChart(projectId),
  });
}

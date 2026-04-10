import { useQuery } from "@tanstack/react-query";
import { getSiteStats } from "../api/site";
import type { SiteStats } from "../types";

export function useSiteStats() {
  return useQuery<SiteStats>({
    queryKey: ["site-stats"],
    queryFn: getSiteStats,
    staleTime: 60_000,
  });
}

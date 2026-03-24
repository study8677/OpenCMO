import { useQuery } from "@tanstack/react-query";
import { listCampaigns, getCampaign } from "../api/campaigns";
import type { CampaignRun } from "../api/campaigns";

export function useCampaigns(projectId: number) {
  return useQuery<CampaignRun[]>({
    queryKey: ["campaigns", projectId],
    queryFn: () => listCampaigns(projectId),
  });
}

export function useCampaign(runId: number) {
  return useQuery<CampaignRun>({
    queryKey: ["campaign", runId],
    queryFn: () => getCampaign(runId),
    enabled: runId > 0,
  });
}

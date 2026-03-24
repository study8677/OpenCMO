import { apiJson } from "./client";

export interface CampaignArtifact {
  id: number;
  artifact_type: string;
  channel: string | null;
  title: string;
  content: string;
  created_at: string;
}

export interface CampaignRun {
  id: number;
  project_id: number;
  goal: string;
  channels: string[];
  status: string;
  created_at: string;
  completed_at: string | null;
  artifact_count?: number;
  artifacts?: CampaignArtifact[];
}

export function listCampaigns(projectId: number): Promise<CampaignRun[]> {
  return apiJson<CampaignRun[]>(`/projects/${projectId}/campaigns`);
}

export function getCampaign(runId: number): Promise<CampaignRun> {
  return apiJson<CampaignRun>(`/campaigns/${runId}`);
}

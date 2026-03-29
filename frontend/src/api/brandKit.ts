import { apiJson } from "./client";

export interface BrandKit {
  project_id: number;
  tone_of_voice: string;
  target_audience: string;
  core_values: string;
  forbidden_words: string[];
  best_examples: string;
  custom_instructions: string;
  updated_at: string | null;
}

export function getBrandKit(projectId: number): Promise<BrandKit> {
  return apiJson<BrandKit>(`/projects/${projectId}/brand-kit`);
}

export function saveBrandKit(projectId: number, kit: Partial<BrandKit>): Promise<BrandKit> {
  return apiJson<BrandKit>(`/projects/${projectId}/brand-kit`, {
    method: "PUT",
    body: JSON.stringify(kit),
  });
}

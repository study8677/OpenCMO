import { apiJson } from "./client";
import type { AISettings } from "../types";

export function getSettings(): Promise<AISettings> {
  return apiJson<AISettings>("/settings");
}

export function saveSettings(data: {
  OPENAI_API_KEY?: string;
  OPENAI_BASE_URL?: string;
  OPENCMO_MODEL_DEFAULT?: string;
}): Promise<{ ok: boolean }> {
  return apiJson("/settings", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

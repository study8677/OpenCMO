import { apiJson } from "./client";
import type { Monitor, TaskRecord } from "../types";

export function listMonitors(): Promise<Monitor[]> {
  return apiJson<Monitor[]>("/monitors");
}

export function createMonitor(data: {
  url: string;
}): Promise<{ project_id: number; monitor_id: number; keywords_added: string[]; task_id?: string }> {
  return apiJson("/monitors", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteMonitor(id: number): Promise<{ ok: boolean }> {
  return apiJson(`/monitors/${id}`, { method: "DELETE" });
}

export function runMonitor(id: number): Promise<TaskRecord> {
  return apiJson<TaskRecord>(`/monitors/${id}/run`, { method: "POST" });
}

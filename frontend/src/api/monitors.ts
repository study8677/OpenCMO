import { apiJson } from "./client";
import type { Monitor, MonitorRun, TaskRecord } from "../types";

export function listMonitors(): Promise<Monitor[]> {
  return apiJson<Monitor[]>("/monitors");
}

export function createMonitor(data: {
  url: string;
  locale?: string;
  cron_expr?: string;
}): Promise<{ project_id: number; monitor_id: number; keywords_added: string[]; task_id?: string }> {
  return apiJson("/monitors", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateMonitor(
  id: number,
  data: { cron_expr?: string; enabled?: boolean },
): Promise<{ ok: boolean }> {
  return apiJson(`/monitors/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteMonitor(id: number): Promise<{ ok: boolean }> {
  return apiJson(`/monitors/${id}`, { method: "DELETE" });
}

export function runMonitor(id: number, locale?: string): Promise<TaskRecord> {
  return apiJson<TaskRecord>(`/monitors/${id}/run`, {
    method: "POST",
    body: JSON.stringify(locale ? { locale } : {}),
  });
}

export function getMonitorRuns(monitorId: number): Promise<MonitorRun[]> {
  return apiJson<MonitorRun[]>(`/monitors/${monitorId}/runs`);
}

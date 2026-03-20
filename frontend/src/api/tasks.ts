import { apiJson } from "./client";
import type { TaskRecord } from "../types";

export function getTask(taskId: string): Promise<TaskRecord> {
  return apiJson<TaskRecord>(`/tasks/${taskId}`);
}

export function listTasks(): Promise<TaskRecord[]> {
  return apiJson<TaskRecord[]>("/tasks");
}

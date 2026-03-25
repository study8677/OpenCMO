import { apiJson } from "./client";

export type InsightSeverity = "critical" | "warning" | "info";
export type InsightActionType = "navigate" | "chat" | "api_call";

export interface InsightActionParams {
  route?: string;
  url?: string;
  prompt?: string;
  endpoint?: string;
  [key: string]: unknown;
}

export interface InsightRecord {
  id: number;
  project_id: number;
  insight_type: string;
  severity: InsightSeverity;
  title: string;
  summary: string;
  action_type: InsightActionType | string;
  action_params: InsightActionParams;
  read: boolean;
  created_at: string;
}

export interface InsightSummaryItem {
  id: number;
  project_id: number;
  insight_type: string;
  severity: InsightSeverity;
  title: string;
  summary: string;
  action_type: InsightActionType | string;
  action_params: InsightActionParams;
  created_at: string;
}

export interface InsightsSummary {
  unread_count: number;
  recent: InsightSummaryItem[];
}

type RawInsightActionParams = InsightActionParams | string | null;

interface RawInsightRecord
  extends Omit<InsightRecord, "action_params"> {
  action_params: RawInsightActionParams;
}

interface RawInsightSummaryItem
  extends Omit<InsightSummaryItem, "action_params"> {
  action_params: RawInsightActionParams;
}

interface RawInsightsSummary {
  unread_count: number;
  recent: RawInsightSummaryItem[];
}

function buildInsightsQuery(projectId?: number, unread = false): string {
  const params = new URLSearchParams();

  if (typeof projectId === "number") {
    params.set("project_id", String(projectId));
  }
  if (unread) {
    params.set("unread", "true");
  }

  const query = params.toString();
  return query ? `?${query}` : "";
}

function parseActionParams(actionParams: RawInsightActionParams): InsightActionParams {
  if (actionParams && typeof actionParams === "object" && !Array.isArray(actionParams)) {
    return actionParams;
  }

  if (typeof actionParams === "string" && actionParams.trim()) {
    try {
      const parsed = JSON.parse(actionParams) as unknown;
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return parsed as InsightActionParams;
      }
    } catch {
      return {};
    }
  }

  return {};
}

function normalizeInsight(raw: RawInsightRecord): InsightRecord {
  return {
    ...raw,
    action_params: parseActionParams(raw.action_params),
  };
}

function normalizeSummaryItem(raw: RawInsightSummaryItem): InsightSummaryItem {
  return {
    ...raw,
    action_params: parseActionParams(raw.action_params),
  };
}

export async function getInsightsSummary(projectId?: number): Promise<InsightsSummary> {
  const data = await apiJson<RawInsightsSummary>(
    `/insights/summary${buildInsightsQuery(projectId)}`,
  );

  return {
    unread_count: data.unread_count,
    recent: data.recent.map(normalizeSummaryItem),
  };
}

export async function getInsights(
  projectId?: number,
  unread = false,
): Promise<InsightRecord[]> {
  const data = await apiJson<RawInsightRecord[]>(
    `/insights${buildInsightsQuery(projectId, unread)}`,
  );

  return data.map(normalizeInsight);
}

export function markInsightRead(id: number): Promise<{ ok: boolean }> {
  return apiJson<{ ok: boolean }>(`/insights/${id}/read`, {
    method: "POST",
  });
}

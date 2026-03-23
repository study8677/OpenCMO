import { apiJson } from "./client";
import type { ApprovalRecord, ApprovalStatus } from "../types";

export function listApprovals(
  status: ApprovalStatus = "pending",
  limit = 20,
): Promise<ApprovalRecord[]> {
  const params = new URLSearchParams({ status, limit: String(limit) });
  return apiJson<ApprovalRecord[]>(`/approvals?${params.toString()}`);
}

export function approveApproval(
  id: number,
  decision_note = "",
): Promise<ApprovalRecord> {
  return apiJson<ApprovalRecord>(`/approvals/${id}/approve`, {
    method: "POST",
    body: JSON.stringify({ decision_note }),
  });
}

export function rejectApproval(
  id: number,
  decision_note = "",
): Promise<ApprovalRecord> {
  return apiJson<ApprovalRecord>(`/approvals/${id}/reject`, {
    method: "POST",
    body: JSON.stringify({ decision_note }),
  });
}

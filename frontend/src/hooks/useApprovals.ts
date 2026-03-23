import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { approveApproval, listApprovals, rejectApproval } from "../api/approvals";
import type { ApprovalStatus } from "../types";

export function useApprovals(status: ApprovalStatus = "pending", limit = 20) {
  return useQuery({
    queryKey: ["approvals", status, limit],
    queryFn: () => listApprovals(status, limit),
  });
}

export function useApproveApproval() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, decision_note = "" }: { id: number; decision_note?: string }) =>
      approveApproval(id, decision_note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] });
    },
  });
}

export function useRejectApproval() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, decision_note = "" }: { id: number; decision_note?: string }) =>
      rejectApproval(id, decision_note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] });
    },
  });
}

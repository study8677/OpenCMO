import { ApprovalCard } from "../components/approval/ApprovalCard";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { useApproveApproval, useApprovals, useRejectApproval } from "../hooks/useApprovals";

export function ApprovalsPage() {
  const approvalsQuery = useApprovals("pending", 20);
  const approveMutation = useApproveApproval();
  const rejectMutation = useRejectApproval();

  const currentApproval = approvalsQuery.data?.[0] ?? null;
  const pendingCount = approvalsQuery.data?.length ?? 0;
  const busy = approveMutation.isPending || rejectMutation.isPending;
  const error = [
    approvalsQuery.error,
    approveMutation.error,
    rejectMutation.error,
  ].find((value): value is Error => value instanceof Error)?.message ?? "";

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out h-full flex flex-col">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">Content Approvals</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Review exact publish payloads before anything leaves OpenCMO.
          </p>
        </div>
        <div className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 shadow-sm">
          {pendingCount} pending
        </div>
      </div>

      {error ? <div className="mb-6"><ErrorAlert message={error} /></div> : null}

      <div className="flex-1 flex flex-col items-center justify-center pb-20">
        {approvalsQuery.isLoading ? (
          <LoadingSpinner className="min-h-[420px]" />
        ) : (
          <ApprovalCard
            approval={currentApproval}
            pendingCount={pendingCount}
            busy={busy}
            onApprove={() => {
              if (currentApproval) {
                approveMutation.mutate({ id: currentApproval.id });
              }
            }}
            onReject={() => {
              if (currentApproval) {
                rejectMutation.mutate({ id: currentApproval.id });
              }
            }}
          />
        )}
      </div>
    </div>
  );
}

import { useState } from "react";
import { AlertTriangle, ExternalLink, Settings } from "lucide-react";
import { ApprovalCard } from "../components/approval/ApprovalCard";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { useApproveApproval, useApprovals, useRejectApproval } from "../hooks/useApprovals";
import { ApiError } from "../api/client";
import { useNavigate } from "react-router";

export function ApprovalsPage() {
  const approvalsQuery = useApprovals("pending", 20);
  const approveMutation = useApproveApproval();
  const rejectMutation = useRejectApproval();
  const navigate = useNavigate();

  const [actionError, setActionError] = useState<{
    message: string;
    errorCode?: string;
  } | null>(null);

  const currentApproval = approvalsQuery.data?.[0] ?? null;
  const pendingCount = approvalsQuery.data?.length ?? 0;
  const busy = approveMutation.isPending || rejectMutation.isPending;
  const queryError = approvalsQuery.error instanceof Error ? approvalsQuery.error.message : "";

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

      {queryError ? <div className="mb-6"><ErrorAlert message={queryError} /></div> : null}

      {/* Contextual error banner for auto_publish_disabled */}
      {actionError?.errorCode === "auto_publish_disabled" ? (
        <div className="mb-6 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50/80 p-4 shadow-sm">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-900">
              Auto-Publish is not enabled
            </p>
            <p className="mt-1 text-sm text-amber-700">
              To publish content to external platforms (Reddit, Twitter, etc.), you need to enable
              <code className="mx-1 rounded bg-amber-100 px-1.5 py-0.5 text-xs font-mono font-bold">OPENCMO_AUTO_PUBLISH</code>
              in Settings.
            </p>
            <button
              onClick={() => navigate("/?tab=settings")}
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-semibold text-amber-800 shadow-sm transition hover:bg-amber-50"
            >
              <Settings className="h-3.5 w-3.5" />
              Go to Settings
              <ExternalLink className="h-3 w-3" />
            </button>
          </div>
          <button
            onClick={() => setActionError(null)}
            className="text-amber-400 hover:text-amber-600 text-lg leading-none"
          >
            ×
          </button>
        </div>
      ) : actionError ? (
        <div className="mb-6"><ErrorAlert message={actionError.message} /></div>
      ) : null}

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
                setActionError(null);
                approveMutation.mutate(
                  { id: currentApproval.id },
                  {
                    onError: (err) => {
                      if (err instanceof ApiError) {
                        setActionError({
                          message: err.message,
                          errorCode: err.errorCode,
                        });
                      } else {
                        setActionError({ message: String(err) });
                      }
                    },
                  },
                );
              }
            }}
            onReject={() => {
              if (currentApproval) {
                setActionError(null);
                rejectMutation.mutate(
                  { id: currentApproval.id },
                  {
                    onError: (err) => {
                      setActionError({
                        message: err instanceof Error ? err.message : String(err),
                      });
                    },
                  },
                );
              }
            }}
          />
        )}
      </div>
    </div>
  );
}

import { Bot, Check, Clock3, ExternalLink, MessageSquare, Send, X } from "lucide-react";
import type { ApprovalRecord } from "../../types";
import { EmptyState } from "../common/EmptyState";

function getPrimaryCopy(approval: ApprovalRecord): string {
  const preview = approval.preview;

  if (typeof preview.text === "string" && preview.text.trim()) {
    return preview.text;
  }
  if (typeof preview.body === "string" && preview.body.trim()) {
    return preview.body;
  }
  return approval.content;
}

function getMetaLabel(approval: ApprovalRecord): string {
  const preview = approval.preview;

  if (typeof preview.subreddit === "string") {
    return `r/${preview.subreddit}`;
  }
  if (typeof preview.parent_id === "string") {
    return `Reply to ${preview.parent_id}`;
  }
  if (typeof preview.length === "number") {
    return `${preview.length} chars`;
  }
  return approval.channel;
}

function getTitle(approval: ApprovalRecord): string {
  const preview = approval.preview;

  if (typeof preview.title === "string" && preview.title.trim()) {
    return preview.title;
  }
  if (approval.title.trim()) {
    return approval.title;
  }
  return approval.approval_type.replace(/_/g, " ");
}

export function ApprovalCard({
  approval,
  pendingCount,
  busy,
  onApprove,
  onReject,
}: {
  approval: ApprovalRecord | null;
  pendingCount: number;
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
}) {
  if (!approval) {
    return (
      <EmptyState
        title="Approval queue is clear"
        description="Queued previews will appear here before anything gets published."
      />
    );
  }

  return (
    <div className="relative mx-auto flex w-full max-w-2xl flex-col items-center justify-center">
      <div className="absolute inset-x-10 top-6 h-full rounded-[2rem] bg-gradient-to-br from-slate-100 to-slate-200/70 opacity-60 blur-sm" />
      <div className="absolute inset-x-6 top-3 h-full rounded-[2rem] border border-slate-200/80 bg-white/60 shadow-lg" />

      <article className="relative w-full overflow-hidden rounded-[2rem] border border-slate-200/70 bg-[radial-gradient(circle_at_top,_rgba(99,102,241,0.12),_transparent_36%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-8 shadow-[0_24px_80px_rgba(15,23,42,0.12)] ring-1 ring-slate-950/5">
        <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 ring-1 ring-indigo-200 shadow-sm">
              <MessageSquare className="h-5 w-5" />
            </span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                {approval.agent_name || "OpenCMO Agent"}
              </p>
              <h2 className="mt-1 text-xl font-semibold text-slate-950">
                {getTitle(approval)}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {approval.source_insight_id && (
              <div className="flex items-center gap-1.5 rounded-full border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-700">
                <Bot className="h-3.5 w-3.5" />
                Autopilot
              </div>
            )}
            <div className="flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700">
              <Clock3 className="h-4 w-4" />
              {pendingCount} pending
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
          <section className="rounded-[1.5rem] border border-slate-200/70 bg-white/80 p-6 shadow-inner">
            <div className="mb-4 flex items-center justify-between gap-3">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                Generated Preview
              </p>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                {getMetaLabel(approval)}
              </span>
            </div>

            <p className="whitespace-pre-wrap text-lg leading-8 text-slate-800">
              {getPrimaryCopy(approval)}
            </p>
          </section>

          <aside className="space-y-4 rounded-[1.5rem] border border-slate-200/70 bg-slate-950/[0.03] p-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                Channel
              </p>
              <p className="mt-2 text-sm font-semibold capitalize text-slate-900">
                {approval.channel.replace(/_/g, " ")}
              </p>
            </div>

            {approval.target_label && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                  Target
                </p>
                <p className="mt-2 text-sm font-medium text-slate-800">
                  {approval.target_label}
                </p>
              </div>
            )}

            {approval.target_url && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                  Target URL
                </p>
                <a
                  href={approval.target_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 flex items-center gap-1 break-all text-sm font-medium text-indigo-600 hover:text-indigo-700"
                >
                  <span>{approval.target_url}</span>
                  <ExternalLink className="h-4 w-4 shrink-0" />
                </a>
              </div>
            )}

            {approval.source_insight_id && approval.preview.why_this && (
              <div className="space-y-2 rounded-xl border border-violet-100 bg-violet-50/50 p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-violet-500">
                  AI Reasoning
                </p>
                <p className="text-xs text-violet-700">
                  <span className="font-semibold">Why this:</span>{" "}
                  {String(approval.preview.why_this)}
                </p>
                {approval.preview.why_now && (
                  <p className="text-xs text-violet-700">
                    <span className="font-semibold">Why now:</span>{" "}
                    {String(approval.preview.why_now)}
                  </p>
                )}
                {approval.preview.why_here && (
                  <p className="text-xs text-violet-700">
                    <span className="font-semibold">Why here:</span>{" "}
                    {String(approval.preview.why_here)}
                  </p>
                )}
              </div>
            )}

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                Created
              </p>
              <p className="mt-2 text-sm text-slate-700">
                {new Date(approval.created_at).toLocaleString()}
              </p>
            </div>
          </aside>
        </div>

        <div className="mt-8 flex items-center justify-center gap-4">
          <button
            onClick={onReject}
            disabled={busy}
            className="group inline-flex h-14 items-center justify-center gap-2 rounded-full border border-rose-200 bg-white px-6 text-sm font-semibold text-rose-600 shadow-sm transition hover:-translate-y-0.5 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <X className="h-4 w-4" />
            Reject
          </button>
          <button
            onClick={onApprove}
            disabled={busy}
            className="group inline-flex h-14 items-center justify-center gap-2 rounded-full bg-emerald-500 px-6 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(16,185,129,0.32)] transition hover:-translate-y-0.5 hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Check className="h-4 w-4" />
            Approve & publish
            <Send className="h-4 w-4" />
          </button>
        </div>
      </article>
    </div>
  );
}

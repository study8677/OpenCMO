import { Loader2 } from "lucide-react";

export function PageLoader() {
  return (
    <div className="flex h-full items-center justify-center min-h-[400px]">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="absolute inset-0 rounded-full bg-brand-500/20 blur-xl animate-pulse" />
          <Loader2
            className="relative h-10 w-10 animate-spin text-brand-500"
            strokeWidth={2}
          />
        </div>
        <p className="text-sm text-slate-400 animate-pulse">Loading…</p>
      </div>
    </div>
  );
}

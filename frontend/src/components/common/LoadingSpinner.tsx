import { Loader2 } from "lucide-react";

export function LoadingSpinner({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center p-12 ${className}`}>
      <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
    </div>
  );
}

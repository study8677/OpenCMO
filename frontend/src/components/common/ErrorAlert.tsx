import { AlertCircle } from "lucide-react";

export function ErrorAlert({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4">
      <AlertCircle className="h-5 w-5 shrink-0 text-rose-500" />
      <p className="text-sm text-rose-700">{message}</p>
    </div>
  );
}

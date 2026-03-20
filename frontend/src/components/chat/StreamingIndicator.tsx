import { useI18n } from "../../i18n";
import { Bot } from "lucide-react";

export function StreamingIndicator() {
  const { t } = useI18n();

  return (
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-slate-100 to-slate-50">
        <Bot size={16} className="text-slate-600" />
      </div>
      <div className="flex items-center gap-2 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-400 ring-1 ring-inset ring-slate-100">
        <div className="flex gap-1">
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
        </div>
        <span>{t("chat.thinking")}</span>
      </div>
    </div>
  );
}

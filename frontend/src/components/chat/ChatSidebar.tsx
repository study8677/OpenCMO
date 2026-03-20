import { Plus, Trash2, MessageSquare } from "lucide-react";
import type { ChatSessionSummary } from "../../types";
import { useI18n } from "../../i18n";

export function ChatSidebar({
  sessions,
  activeSessionId,
  onSelect,
  onDelete,
  onNewChat,
}: {
  sessions: ChatSessionSummary[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onNewChat: () => void;
}) {
  const { t } = useI18n();

  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  const groups: { label: string; items: ChatSessionSummary[] }[] = [];
  const todayItems: ChatSessionSummary[] = [];
  const yesterdayItems: ChatSessionSummary[] = [];
  const olderItems: ChatSessionSummary[] = [];

  for (const s of sessions) {
    const d = new Date(s.updated_at + "Z").toDateString();
    if (d === today) todayItems.push(s);
    else if (d === yesterday) yesterdayItems.push(s);
    else olderItems.push(s);
  }

  if (todayItems.length) groups.push({ label: t("chat.today"), items: todayItems });
  if (yesterdayItems.length) groups.push({ label: t("chat.yesterday"), items: yesterdayItems });
  if (olderItems.length) groups.push({ label: t("chat.older"), items: olderItems });

  return (
    <div className="hidden w-64 shrink-0 flex-col rounded-2xl border border-slate-200 bg-white lg:flex">
      <div className="border-b border-slate-100 p-3">
        <button
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-3 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-indigo-700 hover:shadow-md"
        >
          <Plus size={16} />
          {t("chat.newChat")}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {groups.length === 0 && (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-50">
              <MessageSquare size={18} className="text-slate-300" />
            </div>
            <p className="text-xs text-slate-400">{t("chat.noHistory")}</p>
          </div>
        )}
        {groups.map((group) => (
          <div key={group.label} className="mb-3">
            <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
              {group.label}
            </p>
            {group.items.map((s) => (
              <div
                key={s.id}
                className={`group flex items-center rounded-xl px-2.5 py-2 text-sm transition-all ${
                  s.id === activeSessionId
                    ? "bg-indigo-50 font-medium text-indigo-700"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <button
                  onClick={() => onSelect(s.id)}
                  className="min-w-0 flex-1 truncate text-left"
                >
                  {s.title || t("chat.newChat")}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(s.id);
                  }}
                  className="ml-1 shrink-0 rounded-lg p-1 opacity-0 transition-all hover:bg-rose-50 hover:text-rose-500 group-hover:opacity-100"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

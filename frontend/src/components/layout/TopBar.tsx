import { Menu, Globe, LogOut } from "lucide-react";
import { useAuth } from "../auth/useAuth";
import { useI18n } from "../../i18n";

export function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { isAuthenticated, logout } = useAuth();
  const { locale, setLocale, t } = useI18n();

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur-sm">
      <button className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 lg:hidden" onClick={onMenuClick}>
        <Menu size={20} />
      </button>
      <div className="flex-1" />
      <div className="flex items-center gap-2">
        <button
          onClick={() => setLocale(locale === "en" ? "zh" : "en")}
          className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          <Globe size={14} />
          {locale === "en" ? "中文" : "EN"}
        </button>
        {isAuthenticated && (
          <button
            onClick={logout}
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
          >
            <LogOut size={14} />
            {t("common.logout")}
          </button>
        )}
      </div>
    </header>
  );
}

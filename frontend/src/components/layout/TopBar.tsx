import { Menu, Globe, LogOut } from "lucide-react";
import { useAuth } from "../auth/useAuth";
import { useI18n } from "../../i18n";
import { NotificationBell } from "./NotificationBell";

export function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { isAuthenticated, logout } = useAuth();
  const { locale, setLocale, t } = useI18n();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between bg-white/80 px-4 backdrop-blur-xl transition-colors duration-500">
      <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-all hover:scale-105 active:scale-95 lg:hidden" onClick={onMenuClick}>
        <Menu size={20} />
      </button>
      <div className="flex-1" />
      <div className="flex items-center gap-3 pr-2 lg:pr-4">
        <NotificationBell />
        <button
          onClick={() => setLocale(locale === "en" ? "zh" : "en")}
          className="group flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium text-slate-500 transition-all duration-200 hover:bg-slate-100 hover:text-slate-900 hover:scale-105 active:scale-95"
        >
          <Globe size={16} className="transition-transform group-hover:rotate-12" />
          {locale === "en" ? "中文" : "EN"}
        </button>
        {isAuthenticated && (
          <button
            onClick={logout}
            className="group flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium text-slate-500 transition-all duration-200 hover:bg-slate-100 hover:text-slate-900 hover:scale-105 active:scale-95"
          >
            <LogOut size={16} className="transition-transform group-hover:-translate-x-0.5" />
            {t("common.logout")}
          </button>
        )}
      </div>
    </header>
  );
}

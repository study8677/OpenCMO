import { useState } from "react";
import { Link, useLocation } from "react-router";
import {
  LayoutDashboard,
  MessageSquare,
  CheckSquare,
  FolderOpen,
  Settings,
  X,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { listProjects } from "../../api/projects";
import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";
import { SettingsDialog } from "../settings/SettingsDialog";

const NAV: { to: string; labelKey: TranslationKey; icon: typeof LayoutDashboard }[] = [
  { to: "/", labelKey: "nav.dashboard", icon: LayoutDashboard },
  { to: "/approvals", labelKey: "nav.approvals", icon: CheckSquare },
  { to: "/chat", labelKey: "nav.aiChat", icon: MessageSquare },
];

export function Sidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { pathname } = useLocation();
  const { t } = useI18n();
  const [showSettings, setShowSettings] = useState(false);
  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  return (
    <>
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 transform flex-col bg-[#f9f9f9] border-r border-[#ececec] transition-transform lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-14 items-center justify-between px-4 mt-2">
          <Link to="/" className="text-lg font-semibold text-slate-800 tracking-tight" onClick={onClose}>
            OpenCMO
          </Link>
          <button className="text-slate-400 hover:text-slate-800 transition-colors lg:hidden" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {NAV.map(({ to, labelKey, icon: Icon }) => {
            const active = to === "/" ? pathname === to : pathname.startsWith(to);
            return (
              <Link
                key={to}
                to={to}
                onClick={onClose}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-[14px] font-medium transition-all duration-200 ${
                  active
                    ? "bg-black/[0.04] text-slate-900"
                    : "text-slate-600 hover:bg-black/[0.03] hover:text-slate-900 active:scale-[0.98]"
                }`}
              >
                <Icon size={18} className={`transition-colors ${active ? "text-slate-800" : "text-slate-500"}`} />
                {t(labelKey)}
              </Link>
            );
          })}
        </nav>

        {projects && projects.length > 0 && (
          <div className="pt-4 pb-2 px-3">
            <p className="mb-1.5 px-3 text-[11px] font-semibold text-slate-400">
              {t("nav.projects")}
            </p>
            <div className="space-y-0.5">
              {projects.map((p) => (
                <Link
                  key={p.id}
                  to={`/projects/${p.id}`}
                  onClick={onClose}
                  className={`group flex items-center gap-2 rounded-lg px-3 py-1.5 text-[13px] transition-all duration-200 ${
                    pathname === `/projects/${p.id}`
                      ? "bg-black/[0.04] text-slate-900 font-medium"
                      : "text-slate-600 hover:bg-black/[0.03] hover:text-slate-900"
                  }`}
                >
                  <FolderOpen size={14} className="transition-colors text-slate-400 group-hover:text-slate-600" />
                  <span className="truncate">{p.brand_name}</span>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Settings button at bottom */}
        <div className="p-3 mb-2">
          <button
            onClick={() => setShowSettings(true)}
            className="group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-[14px] font-medium text-slate-600 transition-all duration-200 hover:bg-black/[0.03] hover:text-slate-900 active:scale-[0.98]"
          >
            <Settings size={18} className="transition-transform group-hover:rotate-45 text-slate-500 group-hover:text-slate-700" />
            {t("settings.title")}
          </button>
        </div>
      </aside>

      {showSettings && <SettingsDialog onClose={() => setShowSettings(false)} />}
    </>
  );
}

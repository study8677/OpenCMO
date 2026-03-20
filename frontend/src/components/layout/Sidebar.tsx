import { useState } from "react";
import { Link, useLocation } from "react-router";
import {
  LayoutDashboard,
  Radio,
  MessageSquare,
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
  { to: "/monitors", labelKey: "nav.monitors", icon: Radio },
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
        className={`fixed inset-y-0 left-0 z-30 flex w-64 transform flex-col bg-gradient-to-b from-slate-900 to-slate-800 shadow-xl transition-transform lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-14 items-center justify-between border-b border-slate-700/50 px-4">
          <Link to="/" className="text-lg font-bold text-white" onClick={onClose}>
            OpenCMO
          </Link>
          <button className="text-slate-400 hover:text-white lg:hidden" onClick={onClose}>
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
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                  active
                    ? "bg-indigo-500/20 text-white shadow-sm"
                    : "text-slate-400 hover:bg-slate-700/50 hover:text-white"
                }`}
              >
                <Icon size={18} className={active ? "text-indigo-400" : ""} />
                {t(labelKey)}
              </Link>
            );
          })}
        </nav>

        {projects && projects.length > 0 && (
          <div className="border-t border-slate-700/50 p-3">
            <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
              {t("nav.projects")}
            </p>
            <div className="space-y-0.5">
              {projects.map((p) => (
                <Link
                  key={p.id}
                  to={`/projects/${p.id}`}
                  onClick={onClose}
                  className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-all duration-150 ${
                    pathname === `/projects/${p.id}`
                      ? "bg-slate-700/60 text-white"
                      : "text-slate-400 hover:bg-slate-700/40 hover:text-slate-200"
                  }`}
                >
                  <FolderOpen size={14} />
                  <span className="truncate">{p.brand_name}</span>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Settings button at bottom */}
        <div className="border-t border-slate-700/50 p-3">
          <button
            onClick={() => setShowSettings(true)}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-400 transition-all duration-150 hover:bg-slate-700/50 hover:text-white"
          >
            <Settings size={18} />
            {t("settings.title")}
          </button>
        </div>
      </aside>

      {showSettings && <SettingsDialog onClose={() => setShowSettings(false)} />}
    </>
  );
}

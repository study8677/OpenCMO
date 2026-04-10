import { useEffect, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./Sidebar";
import { SiteFooter } from "./SiteFooter";
import { TopBar } from "./TopBar";

export function AppShell({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const robotsMeta = document.querySelector('meta[name="robots"]');
    const previousRobots = robotsMeta?.getAttribute("content") ?? null;
    const previousTitle = document.title;

    if (robotsMeta) {
      robotsMeta.setAttribute("content", "noindex,nofollow");
    }
    document.title = "OpenCMO Workspace";

    return () => {
      if (robotsMeta && previousRobots) {
        robotsMeta.setAttribute("content", previousRobots);
      }
      document.title = previousTitle;
    };
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-white text-slate-800 transition-colors duration-500 font-sans">
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex flex-1 flex-col overflow-hidden lg:pl-0 pl-0 relative">
        <TopBar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto px-4 pb-8 lg:px-8">
          <div className="mx-auto flex min-h-full w-full max-w-5xl flex-col">
            <div className="flex-1">
              {children}
            </div>
            <SiteFooter />
          </div>
        </main>
      </div>
    </div>
  );
}

import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router";
import { AppShell } from "./components/layout/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectPage } from "./pages/ProjectPage";
import { SeoPage } from "./pages/SeoPage";
import { GeoPage } from "./pages/GeoPage";
import { SerpPage } from "./pages/SerpPage";
import { CommunityPage } from "./pages/CommunityPage";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { BrandKitPage } from "./pages/BrandKitPage";

// Heavy pages lazy-loaded: Three.js graph, react-markdown reports/chat, recharts performance
const GraphPage = lazy(() =>
  import("./pages/GraphPage").then((m) => ({ default: m.GraphPage }))
);
const ReportsPage = lazy(() =>
  import("./pages/ReportsPage").then((m) => ({ default: m.ReportsPage }))
);
const ChatPage = lazy(() =>
  import("./pages/ChatPage").then((m) => ({ default: m.ChatPage }))
);
const PerformancePage = lazy(() =>
  import("./pages/PerformancePage").then((m) => ({
    default: m.PerformancePage,
  }))
);

function LazyFallback() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent" />
    </div>
  );
}

function AppRoutes() {
  return (
    <AppShell>
      <Suspense fallback={<LazyFallback />}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/approvals" element={<ApprovalsPage />} />
          <Route path="/projects/:id" element={<ProjectPage />} />
          <Route path="/projects/:id/reports" element={<ReportsPage />} />
          <Route path="/projects/:id/brand-kit" element={<BrandKitPage />} />
          <Route
            path="/projects/:id/performance"
            element={<PerformancePage />}
          />
          <Route path="/projects/:id/seo" element={<SeoPage />} />
          <Route path="/projects/:id/geo" element={<GeoPage />} />
          <Route path="/projects/:id/serp" element={<SerpPage />} />
          <Route path="/projects/:id/community" element={<CommunityPage />} />
          <Route path="/projects/:id/graph" element={<GraphPage />} />
<Route path="/chat" element={<ChatPage />} />
        </Routes>
      </Suspense>
    </AppShell>
  );
}

export default function App() {
  return (
    <BrowserRouter basename="/">
      <AppRoutes />
    </BrowserRouter>
  );
}

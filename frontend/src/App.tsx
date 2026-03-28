import { BrowserRouter, Routes, Route } from "react-router";
import { AppShell } from "./components/layout/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectPage } from "./pages/ProjectPage";
import { SeoPage } from "./pages/SeoPage";
import { GeoPage } from "./pages/GeoPage";
import { SerpPage } from "./pages/SerpPage";
import { CommunityPage } from "./pages/CommunityPage";
import { GraphPage } from "./pages/GraphPage";
import { MonitorsPage } from "./pages/MonitorsPage";
import { ChatPage } from "./pages/ChatPage";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { ReportsPage } from "./pages/ReportsPage";

function AppRoutes() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/approvals" element={<ApprovalsPage />} />
        <Route path="/projects/:id" element={<ProjectPage />} />
        <Route path="/projects/:id/reports" element={<ReportsPage />} />
        <Route path="/projects/:id/seo" element={<SeoPage />} />
        <Route path="/projects/:id/geo" element={<GeoPage />} />
        <Route path="/projects/:id/serp" element={<SerpPage />} />
        <Route path="/projects/:id/community" element={<CommunityPage />} />
        <Route path="/projects/:id/graph" element={<GraphPage />} />
        <Route path="/monitors" element={<MonitorsPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </AppShell>
  );
}

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <AppRoutes />
    </BrowserRouter>
  );
}

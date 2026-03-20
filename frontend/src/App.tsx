import { BrowserRouter, Routes, Route } from "react-router";
import { AppShell } from "./components/layout/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectPage } from "./pages/ProjectPage";
import { SeoPage } from "./pages/SeoPage";
import { GeoPage } from "./pages/GeoPage";
import { SerpPage } from "./pages/SerpPage";
import { CommunityPage } from "./pages/CommunityPage";
import { MonitorsPage } from "./pages/MonitorsPage";
import { ChatPage } from "./pages/ChatPage";
import { TokenPrompt } from "./components/auth/TokenPrompt";
import { useAuth } from "./components/auth/useAuth";

function AppRoutes() {
  const { isAuthenticated, needsAuth } = useAuth();

  if (needsAuth && !isAuthenticated) {
    return <TokenPrompt />;
  }

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/projects/:id" element={<ProjectPage />} />
        <Route path="/projects/:id/seo" element={<SeoPage />} />
        <Route path="/projects/:id/geo" element={<GeoPage />} />
        <Route path="/projects/:id/serp" element={<SerpPage />} />
        <Route path="/projects/:id/community" element={<CommunityPage />} />
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

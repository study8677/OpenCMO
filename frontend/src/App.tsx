import { lazy, Suspense, type ReactNode } from "react";
import { BrowserRouter, Routes, Route } from "react-router";
import { AppShell } from "./components/layout/AppShell";
import { PublicLocaleSync } from "./components/marketing/PublicLocaleSync";
import { LandingPage } from "./pages/LandingPage";
import { PublicServicePage, type PublicServicePageKind } from "./pages/PublicServicePage";
import { BlogPage } from "./pages/BlogPage";
import { BlogArticlePage } from "./pages/BlogArticlePage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectPage } from "./pages/ProjectPage";
import { SampleAuditPage } from "./pages/SampleAuditPage";
import { SeoPage } from "./pages/SeoPage";
import { GeoPage } from "./pages/GeoPage";
import { SerpPage } from "./pages/SerpPage";
import { CommunityPage } from "./pages/CommunityPage";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { BrandKitPage } from "./pages/BrandKitPage";
import { ProjectMonitorsPage } from "./pages/ProjectMonitorsPage";
import { GitHubLeadsPage } from "./pages/GitHubLeadsPage";
import { ContentPage } from "./pages/ContentPage";

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

function LocalizedPublicPage({
  locale,
  children,
}: {
  locale: "en" | "zh";
  children: ReactNode;
}) {
  return (
    <PublicLocaleSync locale={locale}>
      {children}
    </PublicLocaleSync>
  );
}

function AppRoutes() {
  const localizedService = (locale: "en" | "zh", kind: PublicServicePageKind) => (
    <LocalizedPublicPage locale={locale}>
      <PublicServicePage kind={kind} />
    </LocalizedPublicPage>
  );

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/en" element={<LocalizedPublicPage locale="en"><LandingPage /></LocalizedPublicPage>} />
      <Route path="/zh" element={<LocalizedPublicPage locale="zh"><LandingPage /></LocalizedPublicPage>} />
      <Route path="/b2b-leads" element={<PublicServicePage kind="b2b-leads" />} />
      <Route path="/en/b2b-leads" element={localizedService("en", "b2b-leads")} />
      <Route path="/zh/b2b-leads" element={localizedService("zh", "b2b-leads")} />
      <Route path="/seo-geo" element={<PublicServicePage kind="seo-geo" />} />
      <Route path="/en/seo-geo" element={localizedService("en", "seo-geo")} />
      <Route path="/zh/seo-geo" element={localizedService("zh", "seo-geo")} />
      <Route path="/open-source" element={<PublicServicePage kind="open-source" />} />
      <Route path="/en/open-source" element={localizedService("en", "open-source")} />
      <Route path="/zh/open-source" element={localizedService("zh", "open-source")} />
      <Route path="/sample-data" element={<PublicServicePage kind="sample-data" />} />
      <Route path="/en/sample-data" element={localizedService("en", "sample-data")} />
      <Route path="/zh/sample-data" element={localizedService("zh", "sample-data")} />
      <Route path="/contact" element={<PublicServicePage kind="contact" />} />
      <Route path="/en/contact" element={localizedService("en", "contact")} />
      <Route path="/zh/contact" element={localizedService("zh", "contact")} />
      <Route path="/data-policy" element={<PublicServicePage kind="data-policy" />} />
      <Route path="/en/data-policy" element={localizedService("en", "data-policy")} />
      <Route path="/zh/data-policy" element={localizedService("zh", "data-policy")} />
      <Route path="/sample-audit" element={<SampleAuditPage />} />
      <Route path="/en/sample-audit" element={<LocalizedPublicPage locale="en"><SampleAuditPage /></LocalizedPublicPage>} />
      <Route path="/zh/sample-audit" element={<LocalizedPublicPage locale="zh"><SampleAuditPage /></LocalizedPublicPage>} />
      <Route path="/blog" element={<BlogPage />} />
      <Route path="/en/blog" element={<LocalizedPublicPage locale="en"><BlogPage /></LocalizedPublicPage>} />
      <Route path="/zh/blog" element={<LocalizedPublicPage locale="zh"><BlogPage /></LocalizedPublicPage>} />
      <Route path="/blog/:slug" element={<BlogArticlePage />} />
      <Route path="/en/blog/:slug" element={<LocalizedPublicPage locale="en"><BlogArticlePage /></LocalizedPublicPage>} />
      <Route path="/zh/blog/:slug" element={<LocalizedPublicPage locale="zh"><BlogArticlePage /></LocalizedPublicPage>} />
      <Route
        path="*"
        element={(
          <AppShell>
            <Suspense fallback={<LazyFallback />}>
              <Routes>
                <Route path="/workspace" element={<DashboardPage />} />
                <Route path="/approvals" element={<ApprovalsPage />} />
                <Route path="/projects/:id" element={<ProjectPage />} />
                <Route path="/projects/:id/reports" element={<ReportsPage />} />
                <Route path="/projects/:id/content" element={<ContentPage />} />
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
                <Route path="/projects/:id/monitors" element={<ProjectMonitorsPage />} />
                <Route path="/projects/:id/github-leads" element={<GitHubLeadsPage />} />
                <Route path="/chat" element={<ChatPage />} />
              </Routes>
            </Suspense>
          </AppShell>
        )}
      />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter basename="/">
      <AppRoutes />
    </BrowserRouter>
  );
}

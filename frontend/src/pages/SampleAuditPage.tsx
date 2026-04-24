import { ArrowRight, Bot, CheckCircle2, GitBranch, Globe, MessageSquareText, Search } from "lucide-react";
import { Link } from "react-router";
import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SiteFooter } from "../components/layout/SiteFooter";
import { ProjectCommandCenter } from "../components/project/ProjectCommandCenter";
import { ScorePanel } from "../components/project/ScorePanel";
import { useI18n } from "../i18n";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import type { LatestReports, LatestScans, MonitoringSummary, Project, ReportRecord } from "../types";
import type { NextAction } from "../api/projects";
import { getSampleAuditPath, type PublicNavItem } from "../content/marketing";
import { getSeoLocaleFromLocale } from "../utils/publicRoutes";

const SAMPLE_PROJECT: Project = {
  id: 9001,
  brand_name: "FluxKV",
  url: "https://fluxkv.dev",
  category: "Open-source feature flagging for developers",
};

const SAMPLE_LATEST: LatestScans = {
  seo: { scanned_at: "2026-04-13T09:30:00Z", score: 0.58 },
  geo: { scanned_at: "2026-04-13T09:34:00Z", score: 42 },
  community: { scanned_at: "2026-04-13T09:36:00Z", total_hits: 18 },
  serp: [
    { keyword: "open-source feature flags", position: 11, checked_at: "2026-04-13T09:32:00Z" },
    { keyword: "self-hosted feature flags", position: 14, checked_at: "2026-04-13T09:32:00Z" },
    { keyword: "flagsmith alternative", position: 9, checked_at: "2026-04-13T09:32:00Z" },
    { keyword: "feature flags for Kubernetes", position: 17, checked_at: "2026-04-13T09:32:00Z" },
  ],
};

const SAMPLE_MONITORING: MonitoringSummary = {
  run_id: 118,
  status: "completed",
  summary: "Sample audit generated from a seeded full-monitoring run.",
  created_at: "2026-04-13T09:28:00Z",
  completed_at: "2026-04-13T09:39:00Z",
  findings_count: 7,
  recommendations_count: 5,
};

const SAMPLE_REPORT_HUMAN: ReportRecord = {
  id: 901,
  project_id: 9001,
  kind: "strategic",
  audience: "human",
  version: 3,
  is_latest: true,
  source_run_id: 118,
  window_start: "2026-04-06T00:00:00Z",
  window_end: "2026-04-13T00:00:00Z",
  generation_status: "completed",
  status: "completed",
  content: "Sample strategic report content.",
  content_html: "<p>Sample strategic report content.</p>",
  meta: { window_days: 7, sample_count: 18 },
  created_at: "2026-04-13T09:42:00Z",
};

const SAMPLE_REPORTS: LatestReports = {
  strategic: {
    human: SAMPLE_REPORT_HUMAN,
    agent: { ...SAMPLE_REPORT_HUMAN, id: 902, audience: "agent" },
  },
  periodic: {
    human: null,
    agent: null,
  },
};

const SAMPLE_ACTIONS: NextAction[] = [
  {
    domain: "seo",
    priority: "high",
    icon: "search",
    title: "Cut docs landing LCP under 2.5s and add product schema to core pages.",
    description: "This improves both search crawl quality and the credibility of product summaries in AI answers.",
  },
  {
    domain: "geo",
    priority: "high",
    icon: "globe",
    title: "Publish a comparison page that answers “FluxKV vs Flagsmith / Unleash” directly.",
    description: "Assistants currently describe the category with competitor language first and miss the self-hosting story.",
  },
  {
    domain: "community",
    priority: "medium",
    icon: "users",
    title: "Reply in three active threads where teams are comparing self-hosted feature flag options.",
    description: "The best opportunities are already live in public channels and can convert quickly with founder-level replies.",
  },
  {
    domain: "graph",
    priority: "medium",
    icon: "git-branch",
    title: "Track Flagsmith, Unleash, and GrowthBook messaging side-by-side before writing the next launch page.",
    description: "You need a sharper stance on deployment model, OpenFeature support, and rollout governance.",
  },
];

const SAMPLE_NAV: PublicNavItem[] = [
  { href: "#overview", label: "sampleAudit.navOverview" },
  { href: "#seo", label: "sampleAudit.navSeo" },
  { href: "#ai-search", label: "sampleAudit.navAiSearch" },
  { href: "#opportunities", label: "sampleAudit.navOpportunities" },
  { href: "#next-actions", label: "sampleAudit.navActions" },
];

type SampleCardItem = {
  titleKey: string;
  bodyKey: string;
  whyKey: string;
  actionKey: string;
};

const SEO_ITEMS: SampleCardItem[] = [
  {
    titleKey: "sampleAudit.seo1Title",
    bodyKey: "sampleAudit.seo1Body",
    whyKey: "sampleAudit.seo1Why",
    actionKey: "sampleAudit.seo1Action",
  },
  {
    titleKey: "sampleAudit.seo2Title",
    bodyKey: "sampleAudit.seo2Body",
    whyKey: "sampleAudit.seo2Why",
    actionKey: "sampleAudit.seo2Action",
  },
  {
    titleKey: "sampleAudit.seo3Title",
    bodyKey: "sampleAudit.seo3Body",
    whyKey: "sampleAudit.seo3Why",
    actionKey: "sampleAudit.seo3Action",
  },
];

const AI_SEARCH_ITEMS: SampleCardItem[] = [
  {
    titleKey: "sampleAudit.ai1Title",
    bodyKey: "sampleAudit.ai1Body",
    whyKey: "sampleAudit.ai1Why",
    actionKey: "sampleAudit.ai1Action",
  },
  {
    titleKey: "sampleAudit.ai2Title",
    bodyKey: "sampleAudit.ai2Body",
    whyKey: "sampleAudit.ai2Why",
    actionKey: "sampleAudit.ai2Action",
  },
  {
    titleKey: "sampleAudit.ai3Title",
    bodyKey: "sampleAudit.ai3Body",
    whyKey: "sampleAudit.ai3Why",
    actionKey: "sampleAudit.ai3Action",
  },
];

const COMMUNITY_ITEMS = [
  {
    channelKey: "sampleAudit.community1Channel",
    titleKey: "sampleAudit.community1Title",
    bodyKey: "sampleAudit.community1Body",
    actionKey: "sampleAudit.community1Action",
  },
  {
    channelKey: "sampleAudit.community2Channel",
    titleKey: "sampleAudit.community2Title",
    bodyKey: "sampleAudit.community2Body",
    actionKey: "sampleAudit.community2Action",
  },
  {
    channelKey: "sampleAudit.community3Channel",
    titleKey: "sampleAudit.community3Title",
    bodyKey: "sampleAudit.community3Body",
    actionKey: "sampleAudit.community3Action",
  },
];

const COMPETITOR_ITEMS = [
  {
    name: "Flagsmith",
    focusKey: "sampleAudit.competitor1Focus",
    riskKey: "sampleAudit.competitor1Risk",
    openingKey: "sampleAudit.competitor1Opening",
  },
  {
    name: "Unleash",
    focusKey: "sampleAudit.competitor2Focus",
    riskKey: "sampleAudit.competitor2Risk",
    openingKey: "sampleAudit.competitor2Opening",
  },
  {
    name: "GrowthBook",
    focusKey: "sampleAudit.competitor3Focus",
    riskKey: "sampleAudit.competitor3Risk",
    openingKey: "sampleAudit.competitor3Opening",
  },
];

const SHIP_ITEMS = [
  "sampleAudit.ship1",
  "sampleAudit.ship2",
  "sampleAudit.ship3",
  "sampleAudit.ship4",
] as const;

function SampleAuditCard({
  title,
  summary,
  why,
  action,
  whyLabel,
  actionLabel,
}: {
  title: string;
  summary: string;
  why: string;
  action: string;
  whyLabel: string;
  actionLabel: string;
}) {
  return (
    <article className="rounded-[1.8rem] border border-slate-200/80 bg-white/92 p-5 shadow-sm">
      <h3 className="text-lg font-semibold tracking-tight text-slate-950">{title}</h3>
      <p className="mt-3 text-sm leading-7 text-slate-700">{summary}</p>
      <div className="mt-4 rounded-2xl bg-slate-50 px-4 py-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{whyLabel}</p>
        <p className="mt-2 text-sm leading-6 text-slate-700">{why}</p>
      </div>
      <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50/70 px-4 py-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-700">{actionLabel}</p>
        <p className="mt-2 text-sm font-medium leading-6 text-slate-900">{action}</p>
      </div>
    </article>
  );
}

export function SampleAuditPage() {
  const { t, locale } = useI18n();
  const seoLocale = getSeoLocaleFromLocale(locale);
  const sampleAuditPath = getSampleAuditPath(seoLocale);

  usePublicPageMetadata({
    title: t("sampleAudit.metaTitle"),
    description: t("sampleAudit.metaDescription"),
    basePath: "/sample-audit",
  });

  return (
    <div className="min-h-screen bg-[#f6efe5] text-slate-950">
      <PublicSiteHeader items={SAMPLE_NAV} theme="light" />

      <main className="pb-16">
        <section className="mx-auto max-w-7xl px-4 pt-12 lg:px-8">
          <div className="overflow-hidden rounded-[2.4rem] border border-black/8 bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.12),_transparent_32%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] px-6 py-8 shadow-[0_20px_70px_rgba(8,32,50,0.08)] sm:px-8 sm:py-10">
            <div className="flex flex-wrap items-center gap-3">
              <span className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-white">
                <Bot size={14} />
                {t("sampleAudit.badge")}
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                {t("sampleAudit.demoLabel")}
              </span>
            </div>

            <div className="mt-6 grid gap-8 lg:grid-cols-[minmax(0,1.05fr)_minmax(320px,0.95fr)]">
              <div>
                <h1 className="font-display text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                  {t("sampleAudit.title")}
                </h1>
                <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-700">
                  {t("sampleAudit.subtitle")}
                </p>
                <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-500">
                  {t("sampleAudit.note")}
                </p>

                <div className="mt-6 flex flex-wrap gap-3">
                  <a
                    href="#next-actions"
                    className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-slate-800"
                  >
                    {t("sampleAudit.jumpCta")}
                    <ArrowRight size={16} />
                  </a>
                  <Link
                    to="/workspace"
                    className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:border-slate-300 hover:bg-slate-50"
                  >
                    {t("sampleAudit.runCta")}
                  </Link>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  { icon: Search, title: "sampleAudit.metric1Title", body: "sampleAudit.metric1Body" },
                  { icon: Globe, title: "sampleAudit.metric2Title", body: "sampleAudit.metric2Body" },
                  { icon: GitBranch, title: "sampleAudit.metric3Title", body: "sampleAudit.metric3Body" },
                  { icon: MessageSquareText, title: "sampleAudit.metric4Title", body: "sampleAudit.metric4Body" },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <div
                      key={item.title}
                      className="rounded-[1.6rem] border border-slate-200/80 bg-white/92 p-5 shadow-sm"
                    >
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                        <Icon size={18} />
                      </div>
                      <p className="mt-4 text-sm font-semibold text-slate-950">{t(item.title as never)}</p>
                      <p className="mt-2 text-sm leading-6 text-slate-600">{t(item.body as never)}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section id="overview" className="mx-auto max-w-7xl px-4 pt-12 lg:px-8">
          <div className="rounded-[2.2rem] border border-black/8 bg-white/65 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.05)]">
            <ProjectCommandCenter
              projectId={SAMPLE_PROJECT.id}
              latest={SAMPLE_LATEST}
              latestMonitoring={SAMPLE_MONITORING}
              latestReports={SAMPLE_REPORTS}
              competitorCount={COMPETITOR_ITEMS.length}
              pendingApprovals={2}
              actionsOverride={SAMPLE_ACTIONS}
              routeOverrides={{
                changedToday: `${sampleAuditPath}#seo`,
                whatMattersNow: `${sampleAuditPath}#opportunities`,
                readyToShip: `${sampleAuditPath}#next-actions`,
                siteHealth: `${sampleAuditPath}#seo`,
                aiSearch: `${sampleAuditPath}#ai-search`,
                community: `${sampleAuditPath}#opportunities`,
                competitor: `${sampleAuditPath}#competitors`,
                report: `${sampleAuditPath}#next-actions`,
              }}
            />

            <div className="mt-6">
              <ScorePanel latest={SAMPLE_LATEST} latestMonitoring={SAMPLE_MONITORING} />
            </div>
          </div>
        </section>

        <section id="seo" className="mx-auto max-w-7xl px-4 pt-12 lg:px-8">
          <div className="mb-5">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#c96f45]">{t("sampleAudit.navSeo")}</p>
            <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950">
              {t("sampleAudit.seoSectionTitle")}
            </h2>
            <p className="mt-3 max-w-3xl text-base leading-8 text-slate-700">{t("sampleAudit.seoSectionSubtitle")}</p>
          </div>
          <div className="grid gap-5 lg:grid-cols-3">
            {SEO_ITEMS.map((item) => (
              <SampleAuditCard
                key={item.titleKey}
                title={t(item.titleKey as never)}
                summary={t(item.bodyKey as never)}
                why={t(item.whyKey as never)}
                action={t(item.actionKey as never)}
                whyLabel={t("sampleAudit.whyMatters")}
                actionLabel={t("sampleAudit.doNext")}
              />
            ))}
          </div>
        </section>

        <section id="ai-search" className="mx-auto max-w-7xl px-4 pt-12 lg:px-8">
          <div className="mb-5">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#c96f45]">{t("sampleAudit.navAiSearch")}</p>
            <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950">
              {t("sampleAudit.aiSectionTitle")}
            </h2>
            <p className="mt-3 max-w-3xl text-base leading-8 text-slate-700">{t("sampleAudit.aiSectionSubtitle")}</p>
          </div>
          <div className="grid gap-5 lg:grid-cols-3">
            {AI_SEARCH_ITEMS.map((item) => (
              <SampleAuditCard
                key={item.titleKey}
                title={t(item.titleKey as never)}
                summary={t(item.bodyKey as never)}
                why={t(item.whyKey as never)}
                action={t(item.actionKey as never)}
                whyLabel={t("sampleAudit.whyMatters")}
                actionLabel={t("sampleAudit.doNext")}
              />
            ))}
          </div>
        </section>

        <section id="competitors" className="mx-auto max-w-7xl px-4 pt-12 lg:px-8">
          <div className="mb-5">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#c96f45]">{t("sampleAudit.navCompetitors")}</p>
            <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950">
              {t("sampleAudit.competitorSectionTitle")}
            </h2>
            <p className="mt-3 max-w-3xl text-base leading-8 text-slate-700">{t("sampleAudit.competitorSectionSubtitle")}</p>
          </div>
          <div className="grid gap-5 lg:grid-cols-3">
            {COMPETITOR_ITEMS.map((item) => (
              <article key={item.name} className="rounded-[1.8rem] border border-slate-200/80 bg-white/92 p-5 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-lg font-semibold tracking-tight text-slate-950">{item.name}</h3>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    {t("sampleAudit.competitorBadge")}
                  </span>
                </div>
                <div className="mt-4 space-y-3 text-sm leading-6 text-slate-700">
                  <p><span className="font-semibold text-slate-900">{t("sampleAudit.competitorFocusLabel")}:</span> {t(item.focusKey as never)}</p>
                  <p><span className="font-semibold text-slate-900">{t("sampleAudit.competitorRiskLabel")}:</span> {t(item.riskKey as never)}</p>
                  <p><span className="font-semibold text-slate-900">{t("sampleAudit.competitorOpeningLabel")}:</span> {t(item.openingKey as never)}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="opportunities" className="mx-auto max-w-7xl px-4 pt-12 lg:px-8">
          <div className="mb-5">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#c96f45]">{t("sampleAudit.navOpportunities")}</p>
            <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950">
              {t("sampleAudit.opportunitySectionTitle")}
            </h2>
            <p className="mt-3 max-w-3xl text-base leading-8 text-slate-700">{t("sampleAudit.opportunitySectionSubtitle")}</p>
          </div>
          <div className="grid gap-5 lg:grid-cols-3">
            {COMMUNITY_ITEMS.map((item) => (
              <article key={item.titleKey} className="rounded-[1.8rem] border border-slate-200/80 bg-white/92 p-5 shadow-sm">
                <span className="rounded-full bg-amber-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-amber-700">
                  {t(item.channelKey as never)}
                </span>
                <h3 className="mt-4 text-lg font-semibold tracking-tight text-slate-950">{t(item.titleKey as never)}</h3>
                <p className="mt-3 text-sm leading-7 text-slate-700">{t(item.bodyKey as never)}</p>
                <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50/70 px-4 py-3">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-700">{t("sampleAudit.doNext")}</p>
                  <p className="mt-2 text-sm font-medium leading-6 text-slate-900">{t(item.actionKey as never)}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="next-actions" className="mx-auto max-w-7xl px-4 pt-12 lg:px-8">
          <div className="overflow-hidden rounded-[2.2rem] border border-black/8 bg-[#082032] px-6 py-8 text-white shadow-[0_24px_90px_rgba(8,32,50,0.18)] sm:px-8 sm:py-10">
            <div className="grid gap-8 lg:grid-cols-[minmax(0,1.05fr)_minmax(320px,0.95fr)]">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#f3dcc9]">{t("sampleAudit.navActions")}</p>
                <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight">{t("sampleAudit.shipSectionTitle")}</h2>
                <p className="mt-4 max-w-3xl text-base leading-8 text-white/72">{t("sampleAudit.shipSectionSubtitle")}</p>
                <div className="mt-6 space-y-3">
                  {SHIP_ITEMS.map((key) => (
                    <div key={key} className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/8 px-4 py-3 text-sm leading-6 text-white/85">
                      <CheckCircle2 size={16} className="mt-1 shrink-0 text-emerald-300" />
                      <span>{t(key)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[1.8rem] border border-white/10 bg-white/8 p-5">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#f3dcc9]">{t("sampleAudit.reportLabel")}</p>
                <h3 className="mt-3 text-2xl font-semibold tracking-tight">{t("sampleAudit.reportTitle")}</h3>
                <p className="mt-3 text-sm leading-7 text-white/75">{t("sampleAudit.reportBody")}</p>
                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <Link
                    to="/workspace"
                    className="inline-flex items-center justify-center gap-2 rounded-full bg-[#f7ecde] px-4 py-3 text-sm font-semibold text-[#082032] transition-colors hover:bg-white"
                  >
                    {t("sampleAudit.runCta")}
                    <ArrowRight size={15} />
                  </Link>
                  <a
                    href="#overview"
                    className="inline-flex items-center justify-center rounded-full border border-white/14 bg-white/8 px-4 py-3 text-sm font-semibold text-white transition-colors hover:border-white/24 hover:bg-white/12"
                  >
                    {t("sampleAudit.backToOverview")}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SiteFooter variant="public" />
        </div>
      </main>
    </div>
  );
}

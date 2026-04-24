import {
  ArrowRight,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  FileText,
  GitBranch,
  Globe,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router";
import { SiteFooter } from "../components/layout/SiteFooter";
import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SectionReveal } from "../components/marketing/SectionReveal";
import {
  BLOG_ARTICLES,
  BLOG_FEATURED_ARTICLE_SLUG,
  LANDING_CRAWLER_BULLETS,
  LANDING_LEARNING_LOOP_ITEMS,
  LANDING_MENTION_ITEMS,
  LANDING_PLATFORM_ITEMS,
  LANDING_PROOF_ITEMS,
  LANDING_TRUST_ITEMS,
  LANDING_WORKFLOW_STEPS,
  PUBLIC_HOME_NAV,
  getLocalizedBlogArticlePath,
  getSampleAuditPath,
} from "../content/marketing";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { useI18n } from "../i18n";
import type { TranslationKey } from "../i18n";
import { getSeoLocaleFromLocale } from "../utils/publicRoutes";

const PROOF_ICONS = [Search, Bot, Users];
const CAPABILITY_ICONS = [Search, Bot, Users, Globe, FileText];
const LEARNING_LOOP_ICONS = [Search, Bot, CheckCircle2, Sparkles];
const OPEN_SOURCE_ICONS = [GitBranch, ShieldCheck, Globe, FileText];
const TRUST_ICONS = [ShieldCheck, Sparkles, Globe, GitBranch];
const GITHUB_REPO_URL = "https://github.com/study8677/OpenCMO";
const LICENSE_URL = "https://github.com/study8677/OpenCMO/blob/main/LICENSE";
const QUICK_START_URL = "https://github.com/study8677/OpenCMO#quick-start";

export function LandingPage() {
  const { t, locale } = useI18n();
  useEffect(() => {
    if (!window.location.hash) return;

    const targetId = decodeURIComponent(window.location.hash.slice(1));
    const timeoutId = window.setTimeout(() => {
      document.getElementById(targetId)?.scrollIntoView({ block: "start" });
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, []);

  const mentionDateFormatter = new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const seoLocale = getSeoLocaleFromLocale(locale);
  const comparisonArticlePath = getLocalizedBlogArticlePath("opencmo-vs-mautic-posthog", seoLocale);
  const architectureArticlePath = getLocalizedBlogArticlePath("inside-opencmo-workspace", seoLocale);
  const featuredBlogArticle = BLOG_ARTICLES.find((article) => article.slug === BLOG_FEATURED_ARTICLE_SLUG) ?? BLOG_ARTICLES[0]!;
  const heroBadgeKeys = [
    "landing.heroBadgeOpenSource",
    "landing.heroBadgeLicense",
    "landing.heroBadgeSelfHost",
    "landing.heroBadgeByok",
  ] as TranslationKey[];
  const signalStreamKeys = [
    "landing.boardStream1",
    "landing.boardStream2",
    "landing.boardStream3",
  ] as TranslationKey[];
  const pipelineStageKeys = [
    "landing.stage1",
    "landing.stage2",
    "landing.stage3",
    "landing.stage4",
    "landing.stage5",
    "landing.stage6",
  ] as TranslationKey[];
  const mentionPanelKeys = [
    "landing.mentionsPoint1",
    "landing.mentionsPoint2",
    "landing.mentionsPoint3",
  ] as TranslationKey[];
  const learningMemoryRows = [
    {
      label: "landing.learningMemoryRow1Label",
      value: "landing.learningMemoryRow1Value",
    },
    {
      label: "landing.learningMemoryRow2Label",
      value: "landing.learningMemoryRow2Value",
    },
    {
      label: "landing.learningMemoryRow3Label",
      value: "landing.learningMemoryRow3Value",
    },
    {
      label: "landing.learningMemoryRow4Label",
      value: "landing.learningMemoryRow4Value",
    },
  ] as const;
  const learningStats = [
    {
      label: "landing.learningStat1Label",
      value: "landing.learningStat1Value",
    },
    {
      label: "landing.learningStat2Label",
      value: "landing.learningStat2Value",
    },
    {
      label: "landing.learningStat3Label",
      value: "landing.learningStat3Value",
    },
  ] as const;
  const heroMetrics = [
    {
      label: t("landing.metricPipelineLabel"),
      value: t("landing.metricPipelineValue"),
    },
    {
      label: t("landing.metricChannelsLabel"),
      value: t("landing.metricChannelsValue"),
    },
    {
      label: t("landing.metricOutputLabel"),
      value: t("landing.metricOutputValue"),
    },
  ];
  const openSourceLinks = [
    {
      title: "landing.openSourceCardRepoTitle",
      description: "landing.openSourceCardRepoDesc",
      cta: "landing.openSourceCardRepoCta",
      href: GITHUB_REPO_URL,
      external: true,
    },
    {
      title: "landing.openSourceCardLicenseTitle",
      description: "landing.openSourceCardLicenseDesc",
      cta: "landing.openSourceCardLicenseCta",
      href: LICENSE_URL,
      external: true,
    },
    {
      title: "landing.openSourceCardQuickstartTitle",
      description: "landing.openSourceCardQuickstartDesc",
      cta: "landing.openSourceCardQuickstartCta",
      href: QUICK_START_URL,
      external: true,
    },
    {
      title: "landing.openSourceCardArchitectureTitle",
      description: "landing.openSourceCardArchitectureDesc",
      cta: "landing.openSourceCardArchitectureCta",
      href: architectureArticlePath,
      external: false,
    },
  ] as const;

  usePublicPageMetadata({
    title: t("landing.metaTitle"),
    description: t("landing.metaDescription"),
    basePath: "/",
  });

  return (
    <div className="min-h-screen bg-[#f3efe7] text-slate-950">
      <PublicSiteHeader items={PUBLIC_HOME_NAV} theme="light" />

      <main className="overflow-hidden pb-20">
        <section className="relative">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(201,111,69,0.12),transparent_26%),radial-gradient(circle_at_86%_14%,rgba(134,200,188,0.14),transparent_22%),linear-gradient(180deg,#f7f3ec_0%,#f3efe7_54%,#efe7db_100%)]" />
          <div className="absolute -left-12 top-28 h-56 w-56 rounded-full bg-[#c96f45]/12 blur-3xl animate-float-slow" />
          <div className="absolute bottom-10 right-[8%] h-64 w-64 rounded-full bg-[#86c8bc]/14 blur-3xl animate-float-slower" />

          <div className="relative mx-auto grid min-h-[calc(100svh-80px)] max-w-7xl gap-14 px-4 pb-20 pt-10 lg:grid-cols-[minmax(0,0.86fr)_minmax(440px,1.14fr)] lg:px-8 lg:pt-16">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col justify-center pb-6 lg:pb-12"
            >
              <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#9b5d3b]">
                {t("landing.heroEyebrow")}
              </p>
              <h1 className="font-display mt-6 text-[4rem] font-semibold tracking-[-0.08em] text-[#0b1420] sm:text-[5.25rem] lg:text-[6.8rem] lg:leading-[0.92]">
                OpenCMO
              </h1>
              <p className="mt-6 max-w-2xl text-2xl font-semibold leading-[1.2] tracking-tight text-[#0b1420] sm:text-3xl lg:text-[2.8rem]">
                {t("landing.heroTitle")}
              </p>
              <p className="mt-5 max-w-xl text-base leading-8 text-slate-600 sm:text-lg">
                {t("landing.heroSubtitle")}
              </p>

              <div className="mt-9 flex flex-wrap gap-3">
                <Link
                  to="/workspace"
                  className="inline-flex items-center gap-2 rounded-full bg-[#0b1420] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#162131]"
                >
                  {t("landing.primaryCta")}
                  <ArrowRight size={16} />
                </Link>
                <Link
                  to={getSampleAuditPath(seoLocale)}
                  className="inline-flex items-center gap-2 rounded-full border border-black/8 bg-white/72 px-5 py-3 text-sm font-semibold text-slate-900 transition-colors hover:bg-white"
                >
                  {t("landing.sampleCta")}
                </Link>
                <a
                  href={GITHUB_REPO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-full border border-black/8 bg-white/60 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-white hover:text-slate-950"
                >
                  {t("landing.githubCta")}
                  <ArrowUpRight size={16} />
                </a>
              </div>

              <div className="mt-7 flex flex-wrap gap-2">
                {heroBadgeKeys.map((key) => (
                  <span
                    key={key}
                    className="inline-flex items-center rounded-full border border-black/8 bg-white/65 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-600"
                  >
                    {t(key)}
                  </span>
                ))}
              </div>

              <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-sm font-medium text-slate-500">
                {heroMetrics.map((item) => (
                  <div key={item.label} className="flex items-center gap-2">
                    <span className="text-slate-400">{item.label}</span>
                    <span className="font-semibold text-slate-800">{item.value}</span>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 42 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
              className="relative flex items-center justify-center lg:justify-end"
            >
              <div className="absolute left-0 bottom-12 h-44 w-44 rounded-full bg-[#c96f45]/14 blur-3xl" />
              <div className="absolute right-10 top-0 h-40 w-40 rounded-full bg-[#86c8bc]/18 blur-3xl" />

              <div className="relative w-full max-w-[640px]">
                <div className="absolute inset-x-8 top-6 h-full rounded-[2.5rem] bg-[#0b1420]/10 blur-2xl" />
                <div className="relative overflow-hidden rounded-[2.75rem] border border-black/8 bg-[#08131d] p-5 text-white shadow-[0_40px_120px_rgba(8,19,29,0.18)] sm:p-7">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(201,111,69,0.22),transparent_28%),radial-gradient(circle_at_92%_20%,rgba(134,200,188,0.18),transparent_26%),linear-gradient(180deg,rgba(255,255,255,0.05),transparent_40%)]" />

                  <div className="relative">
                    <div className="flex flex-wrap items-start justify-between gap-4 border-b border-white/10 pb-5">
                      <div className="max-w-sm">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#f3dcc9]">
                          {t("landing.previewLabel")}
                        </p>
                        <h2 className="mt-3 text-2xl font-semibold tracking-tight sm:text-[2rem]">
                          {t("landing.previewTitle")}
                        </h2>
                      </div>
                      <div className="rounded-full border border-white/12 bg-white/6 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-white/70">
                        {t("landing.metricPipelineValue")}
                      </div>
                    </div>

                    <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1.06fr)_minmax(220px,0.94fr)]">
                      <div className="rounded-[2rem] border border-white/10 bg-white/5 p-5">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/45">
                          {t("landing.signalBoardEyebrow")}
                        </p>
                        <h3 className="mt-3 text-lg font-semibold tracking-tight">
                          {t("landing.signalBoardTitle")}
                        </h3>
                        <p className="mt-3 text-sm leading-7 text-white/62">
                          {t("landing.signalBoardSummary")}
                        </p>

                        <div className="mt-5 space-y-3">
                          {signalStreamKeys.map((key, index) => (
                            <div
                              key={key}
                              className="rounded-[1.4rem] border border-white/10 bg-[#0c1a26]/80 px-4 py-3"
                            >
                              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/35">
                                0{index + 1}
                              </p>
                              <p className="mt-2 text-sm leading-6 text-white/78">{t(key)}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="rounded-[2rem] border border-white/10 bg-white/5 p-5">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/45">
                          {t("landing.boardStagesTitle")}
                        </p>
                        <div className="mt-5 space-y-3">
                          {pipelineStageKeys.map((key, index) => (
                            <div
                              key={key}
                              className="flex items-center gap-3 border-b border-white/8 pb-3 last:border-b-0 last:pb-0"
                            >
                              <span className="font-mono text-xs text-white/38">
                                {`${index + 1}`.padStart(2, "0")}
                              </span>
                              <span className="text-sm text-white/74">{t(key)}</span>
                            </div>
                          ))}
                        </div>

                        <div className="mt-6 rounded-[1.5rem] border border-emerald-300/20 bg-emerald-400/10 px-4 py-4">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-emerald-200">
                            {t("landing.previewActionLabel")}
                          </p>
                          <p className="mt-2 text-sm leading-6 text-white/88">
                            {t("landing.previewAction")}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-6 grid gap-3 sm:grid-cols-3">
                      {LANDING_PROOF_ITEMS.map((item, index) => {
                        const Icon = PROOF_ICONS[index] ?? Sparkles;
                        return (
                          <div
                            key={item.title}
                            className="rounded-[1.6rem] border border-white/10 bg-white/5 px-4 py-4"
                          >
                            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/8 text-[#f3dcc9]">
                              <Icon size={16} />
                            </div>
                            <p className="mt-3 text-sm font-semibold leading-6 text-white">
                              {t(item.title)}
                            </p>
                            <p className="mt-2 text-sm leading-6 text-white/62">
                              {t(item.description)}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        <section id="product" className="mx-auto max-w-7xl px-4 pt-20 lg:px-8 lg:pt-24">
          <SectionReveal>
            <div className="grid gap-8 lg:grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] lg:items-end">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#9b5d3b]">
                  {t("landing.platformEyebrow")}
                </p>
                <h2 className="font-display mt-4 max-w-xl text-4xl font-semibold tracking-tight text-[#0b1420] sm:text-[3.4rem] sm:leading-[1.02]">
                  {t("landing.platformTitle")}
                </h2>
              </div>
              <p className="max-w-2xl text-lg leading-8 text-slate-600">
                {t("landing.platformSubtitle")}
              </p>
            </div>
          </SectionReveal>

          <div className="mt-16 grid gap-16 lg:grid-cols-[minmax(0,1fr)_400px]">
            <div className="space-y-1">
              {LANDING_PLATFORM_ITEMS.map((item, index) => {
                const Icon = CAPABILITY_ICONS[index] ?? Sparkles;
                return (
                  <SectionReveal key={item.title} delay={index * 0.05}>
                    <article className="grid gap-4 border-t border-black/8 py-8 md:grid-cols-[72px_minmax(0,1fr)] md:gap-6">
                      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white/72 text-slate-700 shadow-[0_10px_30px_rgba(8,19,29,0.06)]">
                        <Icon size={18} />
                      </div>
                      <div className="max-w-3xl">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                          0{index + 1}
                        </p>
                        <h3 className="font-display mt-2 text-2xl font-semibold tracking-tight text-[#0b1420] sm:text-[2.2rem]">
                          {t(item.title)}
                        </h3>
                        <p className="mt-3 text-base leading-8 text-slate-600">
                          {t(item.description)}
                        </p>
                      </div>
                    </article>
                  </SectionReveal>
                );
              })}

              <SectionReveal delay={0.25}>
                <div className="border-t border-black/8 pt-8">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#9b5d3b]">
                    {t("landing.compareEyebrow")}
                  </p>
                  <h3 className="mt-3 text-2xl font-semibold tracking-tight text-[#0b1420]">
                    {t("landing.compareTitle")}
                  </h3>
                  <p className="mt-3 max-w-3xl text-base leading-8 text-slate-600">
                    {t("landing.compareBody")}
                  </p>
                  <Link
                    to={comparisonArticlePath}
                    className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition-colors hover:text-[#9b5d3b]"
                  >
                    {t("landing.compareCta")}
                    <ArrowUpRight size={15} />
                  </Link>
                </div>
              </SectionReveal>
            </div>

            <SectionReveal delay={0.12}>
              <div className="lg:sticky lg:top-24">
                <div className="rounded-[2.4rem] border border-black/8 bg-white/72 p-6 shadow-[0_24px_80px_rgba(8,19,29,0.07)] sm:p-7">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#9b5d3b]">
                    {t("landing.crawlerTitle")}
                  </p>
                  <p className="mt-4 text-base leading-8 text-slate-600">
                    {t("landing.crawlerBody")}
                  </p>

                  <div className="mt-6 space-y-3">
                    {LANDING_CRAWLER_BULLETS.map((key) => (
                      <div
                        key={key}
                        className="flex items-start gap-3 rounded-[1.4rem] border border-black/8 bg-[#f8f4ed] px-4 py-3"
                      >
                        <CheckCircle2 size={16} className="mt-1 shrink-0 text-emerald-700" />
                        <p className="text-sm leading-6 text-slate-700">{t(key)}</p>
                      </div>
                    ))}
                  </div>

                  <div className="mt-7 flex flex-wrap gap-3">
                    <Link
                      to={getSampleAuditPath(seoLocale)}
                      className="inline-flex items-center gap-2 rounded-full bg-[#0b1420] px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#162131]"
                    >
                      {t("landing.sampleCta")}
                      <ArrowRight size={15} />
                    </Link>
                    <a
                      href={QUICK_START_URL}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-full border border-black/8 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:text-slate-950"
                    >
                      {t("landing.openSourceCardQuickstartCta")}
                      <ArrowUpRight size={15} />
                    </a>
                  </div>
                </div>
              </div>
            </SectionReveal>
          </div>
        </section>

        <section id="learning" className="mx-auto max-w-7xl px-4 pt-20 lg:px-8 lg:pt-24">
          <SectionReveal>
            <div className="grid gap-8 lg:grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] lg:items-end">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#9b5d3b]">
                  {t("landing.learningEyebrow")}
                </p>
                <h2 className="font-display mt-4 max-w-2xl text-4xl font-semibold tracking-tight text-[#0b1420] sm:text-[3.4rem] sm:leading-[1.02]">
                  {t("landing.learningTitle")}
                </h2>
              </div>
              <p className="max-w-2xl text-lg leading-8 text-slate-600">
                {t("landing.learningSubtitle")}
              </p>
            </div>
          </SectionReveal>

          <div className="mt-16 grid gap-8 lg:grid-cols-[minmax(0,0.95fr)_minmax(420px,1.05fr)] lg:items-stretch">
            <div className="grid gap-4 sm:grid-cols-2">
              {LANDING_LEARNING_LOOP_ITEMS.map((item, index) => {
                const Icon = LEARNING_LOOP_ICONS[index] ?? Sparkles;
                return (
                  <SectionReveal key={item.title} delay={index * 0.05}>
                    <article className="h-full rounded-[2rem] border border-black/8 bg-white/72 p-6 shadow-[0_18px_60px_rgba(8,19,29,0.05)]">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#0b1420] text-[#f7ecde]">
                          <Icon size={17} />
                        </div>
                        <span className="font-mono text-xs font-semibold text-slate-300">
                          {`${index + 1}`.padStart(2, "0")}
                        </span>
                      </div>
                      <h3 className="mt-5 text-xl font-semibold tracking-tight text-[#0b1420]">
                        {t(item.title)}
                      </h3>
                      <p className="mt-3 text-sm leading-7 text-slate-600">
                        {t(item.description)}
                      </p>
                    </article>
                  </SectionReveal>
                );
              })}
            </div>

            <SectionReveal delay={0.12}>
              <div className="relative h-full overflow-hidden rounded-[2.4rem] bg-[#08131d] p-6 text-white shadow-[0_28px_100px_rgba(8,19,29,0.18)] sm:p-7">
                <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(247,236,222,0.08),transparent_34%),radial-gradient(circle_at_86%_10%,rgba(134,200,188,0.16),transparent_28%)]" />

                <div className="relative">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#f3dcc9]">
                    {t("landing.learningMemoryEyebrow")}
                  </p>
                  <h3 className="mt-3 max-w-md text-3xl font-semibold tracking-tight">
                    {t("landing.learningMemoryTitle")}
                  </h3>
                  <p className="mt-4 max-w-xl text-base leading-8 text-white/66">
                    {t("landing.learningMemoryBody")}
                  </p>

                  <div className="mt-7 space-y-3">
                    {learningMemoryRows.map((row, index) => (
                      <div
                        key={row.label}
                        className="grid gap-3 rounded-[1.4rem] border border-white/10 bg-white/5 px-4 py-4 sm:grid-cols-[120px_minmax(0,1fr)] sm:items-center"
                      >
                        <div className="flex items-center gap-3">
                          <span className="flex h-7 w-7 items-center justify-center rounded-full border border-white/12 bg-white/6 font-mono text-[11px] text-white/46">
                            {`${index + 1}`.padStart(2, "0")}
                          </span>
                          <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/38">
                            {t(row.label)}
                          </span>
                        </div>
                        <p className="text-sm leading-6 text-white/78">{t(row.value)}</p>
                      </div>
                    ))}
                  </div>

                  <div className="mt-6 grid gap-3 sm:grid-cols-3">
                    {learningStats.map((stat) => (
                      <div
                        key={stat.label}
                        className="rounded-[1.3rem] border border-white/10 bg-white/[0.07] px-4 py-4"
                      >
                        <p className="text-2xl font-semibold tracking-tight text-[#f7ecde]">
                          {t(stat.value)}
                        </p>
                        <p className="mt-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-white/38">
                          {t(stat.label)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </SectionReveal>
          </div>
        </section>

        <section id="workflow" className="mt-20 bg-[#08131d] text-white">
          <div className="mx-auto max-w-7xl px-4 py-20 lg:px-8 lg:py-24">
            <div className="grid gap-12 lg:grid-cols-[minmax(0,0.78fr)_minmax(0,1.22fr)]">
              <SectionReveal className="self-start lg:sticky lg:top-24">
                <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#f3dcc9]">
                  {t("landing.workflowEyebrow")}
                </p>
                <h2 className="font-display mt-4 max-w-md text-4xl font-semibold tracking-tight sm:text-[3.4rem] sm:leading-[1.02]">
                  {t("landing.workflowTitle")}
                </h2>
                <p className="mt-5 max-w-md text-lg leading-8 text-white/68">
                  {t("landing.workflowSubtitle")}
                </p>

                <div className="mt-10 space-y-4 border-t border-white/10 pt-6">
                  {heroMetrics.map((item) => (
                    <div key={item.label} className="flex items-center justify-between gap-4 text-sm">
                      <span className="uppercase tracking-[0.16em] text-white/35">
                        {item.label}
                      </span>
                      <span className="font-medium text-white/82">{item.value}</span>
                    </div>
                  ))}
                </div>
              </SectionReveal>

              <div>
                {LANDING_WORKFLOW_STEPS.map((step, index) => (
                  <motion.article
                    key={step.title}
                    initial={{ opacity: 0, x: 24 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true, amount: 0.25 }}
                    transition={{ duration: 0.55, delay: index * 0.06, ease: [0.22, 1, 0.36, 1] }}
                    className="grid gap-4 border-t border-white/10 py-6 md:grid-cols-[84px_minmax(0,1fr)] md:gap-6"
                  >
                    <div className="text-4xl font-semibold tracking-[-0.06em] text-white/24">
                      {`${index + 1}`.padStart(2, "0")}
                    </div>
                    <div className="max-w-3xl">
                      <h3 className="font-display text-2xl font-semibold tracking-tight sm:text-[2rem]">
                        {t(step.title)}
                      </h3>
                      <p className="mt-3 text-base leading-8 text-white/68">
                        {t(step.description)}
                      </p>
                    </div>
                  </motion.article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="open-source" className="mx-auto max-w-7xl px-4 pt-20 lg:px-8 lg:pt-24">
          <SectionReveal>
            <div className="grid gap-8 lg:grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] lg:items-end">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#9b5d3b]">
                  {t("landing.openSourceEyebrow")}
                </p>
                <h2 className="font-display mt-4 max-w-xl text-4xl font-semibold tracking-tight text-[#0b1420] sm:text-[3.4rem] sm:leading-[1.02]">
                  {t("landing.openSourceTitle")}
                </h2>
              </div>
              <p className="max-w-2xl text-lg leading-8 text-slate-600">
                {t("landing.openSourceSubtitle")}
              </p>
            </div>
          </SectionReveal>

          <div className="mt-16 grid gap-8 lg:grid-cols-[minmax(0,1fr)_440px]">
            <div className="overflow-hidden rounded-[2.4rem] border border-black/8 bg-white/72 shadow-[0_24px_80px_rgba(8,19,29,0.07)]">
              {openSourceLinks.map((item, index) => {
                const Icon = OPEN_SOURCE_ICONS[index] ?? Sparkles;
                const content = (
                  <div className="group grid gap-4 px-6 py-6 transition-colors hover:bg-white/55 sm:grid-cols-[60px_minmax(0,1fr)_auto] sm:items-center sm:px-7">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f8f4ed] text-slate-700">
                      <Icon size={18} />
                    </div>
                    <div className="max-w-3xl">
                      <h3 className="font-display text-2xl font-semibold tracking-tight text-[#0b1420]">
                        {t(item.title)}
                      </h3>
                      <p className="mt-2 text-base leading-8 text-slate-600">
                        {t(item.description)}
                      </p>
                    </div>
                    <span className="inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition-transform group-hover:translate-x-0.5">
                      {t(item.cta)}
                      <ArrowUpRight size={15} />
                    </span>
                  </div>
                );

                return item.external ? (
                  <a
                    key={item.title}
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block border-b border-black/8 last:border-b-0"
                  >
                    {content}
                  </a>
                ) : (
                  <Link
                    key={item.title}
                    to={item.href}
                    className="block border-b border-black/8 last:border-b-0"
                  >
                    {content}
                  </Link>
                );
              })}
            </div>

            <SectionReveal delay={0.1}>
              <div className="h-full rounded-[2.4rem] bg-[#0f1a24] p-6 text-white shadow-[0_28px_100px_rgba(8,19,29,0.18)] sm:p-7">
                <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#f3dcc9]">
                  {t("landing.trustEyebrow")}
                </p>
                <h3 className="mt-3 text-3xl font-semibold tracking-tight">
                  {t("landing.trustTitle")}
                </h3>
                <p className="mt-4 text-base leading-8 text-white/68">
                  {t("landing.trustSubtitle")}
                </p>

                <div className="mt-6 space-y-4">
                  {LANDING_TRUST_ITEMS.map((item, index) => {
                    const Icon = TRUST_ICONS[index] ?? ShieldCheck;
                    return (
                      <div
                        key={item.title}
                        className="border-t border-white/10 pt-4 first:border-t-0 first:pt-0"
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/8 text-[#f3dcc9]">
                            <Icon size={16} />
                          </div>
                          <div>
                            <p className="text-lg font-semibold text-white">{t(item.title)}</p>
                            <p className="mt-2 text-sm leading-7 text-white/64">
                              {t(item.description)}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <Link
                  to={comparisonArticlePath}
                  className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-white transition-colors hover:text-[#f3dcc9]"
                >
                  {t("landing.compareCta")}
                  <ArrowUpRight size={15} />
                </Link>
              </div>
            </SectionReveal>
          </div>
        </section>

        <section id="mentions" className="mx-auto max-w-7xl px-4 pt-20 lg:px-8 lg:pt-24">
          <SectionReveal>
            <div className="grid gap-8 lg:grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] lg:items-end">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#9b5d3b]">
                  {t("landing.mentionsEyebrow")}
                </p>
                <h2 className="font-display mt-4 max-w-xl text-4xl font-semibold tracking-tight text-[#0b1420] sm:text-[3.4rem] sm:leading-[1.02]">
                  {t("landing.mentionsTitle")}
                </h2>
              </div>
              <p className="max-w-2xl text-lg leading-8 text-slate-600">
                {t("landing.mentionsSubtitle")}
              </p>
            </div>
          </SectionReveal>

          <div className="mt-16 grid gap-8 lg:grid-cols-[minmax(0,1fr)_400px]">
            <div className="space-y-4">
              {LANDING_MENTION_ITEMS.map((item, index) => (
                <SectionReveal key={item.href} delay={index * 0.06}>
                  <a
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group block rounded-[2rem] border border-black/8 bg-white/72 p-6 shadow-[0_18px_60px_rgba(8,19,29,0.05)] transition-transform duration-300 hover:-translate-y-1 hover:bg-white"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      <span>{t(item.source)}</span>
                      <span>{mentionDateFormatter.format(new Date(item.publishedAt))}</span>
                    </div>
                    <h3 className="font-display mt-4 text-2xl font-semibold tracking-tight text-[#0b1420]">
                      {t(item.title)}
                    </h3>
                    <p className="mt-3 text-base leading-8 text-slate-600">
                      {t(item.description)}
                    </p>
                    <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition-transform group-hover:translate-x-0.5">
                      {t("landing.mentionReadCta")}
                      <ArrowUpRight size={15} />
                    </span>
                  </a>
                </SectionReveal>
              ))}
            </div>

            <SectionReveal delay={0.12}>
              <div className="rounded-[2.4rem] border border-black/8 bg-[#e9dfd1] p-6 shadow-[0_24px_80px_rgba(8,19,29,0.07)] sm:p-7">
                <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#9b5d3b]">
                  {t("landing.mentionsPanelEyebrow")}
                </p>
                <h3 className="mt-3 text-3xl font-semibold tracking-tight text-[#0b1420]">
                  {t("landing.mentionsPanelTitle")}
                </h3>
                <p className="mt-4 text-base leading-8 text-slate-600">
                  {t("landing.mentionsPanelBody")}
                </p>

                <div className="mt-6 space-y-3">
                  {mentionPanelKeys.map((key) => (
                    <div
                      key={key}
                      className="flex items-start gap-3 rounded-[1.4rem] border border-black/8 bg-white/62 px-4 py-3"
                    >
                      <CheckCircle2 size={16} className="mt-1 shrink-0 text-emerald-700" />
                      <p className="text-sm leading-6 text-slate-700">{t(key)}</p>
                    </div>
                  ))}
                </div>

                <Link
                  to={getLocalizedBlogArticlePath(featuredBlogArticle.slug, seoLocale)}
                  className="mt-8 block rounded-[1.8rem] border border-black/8 bg-white/70 p-5 transition-colors hover:bg-white"
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
                    {t("landing.blogPreviewEyebrow")}
                  </p>
                  <h4 className="mt-2 text-xl font-semibold text-[#0b1420]">
                    {t(featuredBlogArticle.title)}
                  </h4>
                  <p className="mt-2 text-sm leading-7 text-slate-600">
                    {t(featuredBlogArticle.summary)}
                  </p>
                  <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-slate-900">
                    {t("blog.readArticleCta")}
                    <ArrowUpRight size={15} />
                  </span>
                </Link>
              </div>
            </SectionReveal>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 pt-20 lg:px-8 lg:pt-24">
          <SectionReveal>
            <div className="relative overflow-hidden rounded-[3rem] bg-[#08131d] px-6 py-10 text-white shadow-[0_28px_100px_rgba(8,19,29,0.18)] sm:px-8 sm:py-12">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(201,111,69,0.22),transparent_28%),radial-gradient(circle_at_88%_20%,rgba(134,200,188,0.14),transparent_24%)]" />

              <div className="relative grid gap-10 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
                <div className="max-w-3xl">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#f3dcc9]">
                    {t("landing.finalEyebrow")}
                  </p>
                  <h2 className="font-display mt-4 text-4xl font-semibold tracking-tight sm:text-[3.4rem] sm:leading-[1.02]">
                    {t("landing.finalTitle")}
                  </h2>
                  <p className="mt-5 text-base leading-8 text-white/68 sm:text-lg">
                    {t("landing.finalSubtitle")}
                  </p>
                </div>

                <div className="flex flex-wrap gap-3">
                  <Link
                    to="/workspace"
                    className="inline-flex items-center gap-2 rounded-full bg-[#f7ecde] px-5 py-3 text-sm font-semibold text-[#082032] transition-colors hover:bg-white"
                  >
                    {t("landing.primaryCta")}
                    <ArrowRight size={16} />
                  </Link>
                  <Link
                    to={getSampleAuditPath(seoLocale)}
                    className="inline-flex items-center gap-2 rounded-full border border-white/14 bg-white/8 px-5 py-3 text-sm font-semibold text-white transition-colors hover:border-white/28 hover:bg-white/12"
                  >
                    {t("landing.sampleCta")}
                  </Link>
                </div>
              </div>
            </div>
          </SectionReveal>
        </section>

        <div className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SiteFooter variant="public" />
        </div>
      </main>
    </div>
  );
}

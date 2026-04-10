import {
  ArrowRight,
  Bot,
  Compass,
  ExternalLink,
  Globe2,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { useEffect } from "react";
import { Link } from "react-router";
import { SiteFooter } from "../components/layout/SiteFooter";
import { useSiteStats } from "../hooks/useSiteStats";
import { useI18n } from "../i18n";
import type { Locale } from "../i18n/I18nProvider";
import type { TranslationKey } from "../i18n";

const GITHUB_REPO = "https://github.com/study8677/OpenCMO";
const LOCALE_CYCLE: Locale[] = ["en", "zh", "ja", "ko", "es"];
const LOCALE_LABELS: Record<Locale, string> = {
  en: "EN",
  zh: "中文",
  ja: "日本語",
  ko: "한국어",
  es: "ES",
};

const CRAWLER_BULLET_KEYS: TranslationKey[] = [
  "landing.crawlerBullet1",
  "landing.crawlerBullet2",
  "landing.crawlerBullet3",
];

const FAQ_ITEMS: Array<{ question: TranslationKey; answer: TranslationKey }> = [
  {
    question: "landing.faq1Question",
    answer: "landing.faq1Answer",
  },
  {
    question: "landing.faq2Question",
    answer: "landing.faq2Answer",
  },
  {
    question: "landing.faq3Question",
    answer: "landing.faq3Answer",
  },
];

export function LandingPage() {
  const { t, locale, setLocale } = useI18n();
  const { data: siteStats } = useSiteStats();
  const numberFormatter = new Intl.NumberFormat(locale);

  useEffect(() => {
    const title = "OpenCMO | Open-Source AI CMO for SEO, GEO, SERP, and Community Monitoring";
    const description = "OpenCMO helps teams monitor SEO, GEO visibility, SERP keywords, and community discussions from one open-source workspace.";
    const previousTitle = document.title;
    const descriptionMeta = document.querySelector('meta[name="description"]');
    const robotsMeta = document.querySelector('meta[name="robots"]');
    const previousDescription = descriptionMeta?.getAttribute("content") ?? null;
    const previousRobots = robotsMeta?.getAttribute("content") ?? null;

    document.title = title;
    if (descriptionMeta) {
      descriptionMeta.setAttribute("content", description);
    }
    if (robotsMeta) {
      robotsMeta.setAttribute("content", "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1");
    }

    return () => {
      document.title = previousTitle;
      if (descriptionMeta && previousDescription) {
        descriptionMeta.setAttribute("content", previousDescription);
      }
      if (robotsMeta && previousRobots) {
        robotsMeta.setAttribute("content", previousRobots);
      }
    };
  }, []);

  const nextLocale = () => {
    const idx = LOCALE_CYCLE.indexOf(locale);
    const next = LOCALE_CYCLE[((idx === -1 ? 0 : idx) + 1) % LOCALE_CYCLE.length] as Locale;
    setLocale(next);
  };

  const capabilities = [
    {
      icon: Search,
      title: t("welcome.featureSeo"),
      description: t("landing.capabilitySeo"),
      accent: "bg-sky-50 text-sky-600",
    },
    {
      icon: Bot,
      title: t("welcome.featureGeo"),
      description: t("landing.capabilityGeo"),
      accent: "bg-emerald-50 text-emerald-600",
    },
    {
      icon: Users,
      title: t("welcome.featureCommunity"),
      description: t("landing.capabilityCommunity"),
      accent: "bg-amber-50 text-amber-600",
    },
  ];

  const proofPoints = [
    {
      icon: Compass,
      title: t("landing.proofResearchTitle"),
      description: t("landing.proofResearchDesc"),
    },
    {
      icon: ShieldCheck,
      title: t("landing.proofCrawlerTitle"),
      description: t("landing.proofCrawlerDesc"),
    },
    {
      icon: Globe2,
      title: t("landing.proofWorkflowTitle"),
      description: t("landing.proofWorkflowDesc"),
    },
  ];

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#f8fafc_0%,#ffffff_45%,#f8fafc_100%)] text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 lg:px-8">
          <Link to="/" className="flex items-center gap-3 text-slate-900">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-sm">
              <Sparkles size={18} />
            </div>
            <div>
              <p className="text-base font-semibold tracking-tight">OpenCMO</p>
              <p className="text-xs text-slate-500">{t("landing.headerTagline")}</p>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            <button
              onClick={nextLocale}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300 hover:text-slate-900"
            >
              {LOCALE_LABELS[locale]}
            </button>
            <a
              href={GITHUB_REPO}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:border-slate-300 hover:text-slate-900 sm:inline-flex"
            >
              {t("siteFooter.sourceCode")}
              <ExternalLink size={14} />
            </a>
            <Link
              to="/workspace"
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-slate-800"
            >
              {t("landing.primaryCta")}
              <ArrowRight size={15} />
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 pb-16 pt-10 lg:px-8 lg:pt-16">
        <section className="grid gap-10 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] lg:items-start">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700">
              <Sparkles size={16} />
              {t("landing.badge")}
            </div>
            <h1 className="mt-6 max-w-4xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
              {t("landing.title")}
            </h1>
            <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-600 sm:text-xl">
              {t("landing.subtitle")}
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/workspace"
                className="inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-slate-800"
              >
                {t("landing.primaryCta")}
                <ArrowRight size={16} />
              </Link>
              <a
                href={GITHUB_REPO}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:border-slate-300 hover:text-slate-900"
              >
                {t("landing.secondaryCta")}
                <ExternalLink size={16} />
              </a>
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-white/90 p-5 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                  {t("siteFooter.totalVisits")}
                </p>
                <p className="mt-2 text-3xl font-semibold text-slate-950">
                  {numberFormatter.format(siteStats?.total_visits ?? 0)}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white/90 p-5 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                  {t("siteFooter.uniqueVisitors")}
                </p>
                <p className="mt-2 text-3xl font-semibold text-slate-950">
                  {numberFormatter.format(siteStats?.unique_visitors ?? 0)}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[2rem] border border-slate-200/80 bg-white/90 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">
              {t("landing.crawlerTitle")}
            </p>
            <p className="mt-3 text-base leading-7 text-slate-600">
              {t("landing.crawlerBody")}
            </p>
            <div className="mt-6 space-y-3">
              {CRAWLER_BULLET_KEYS.map((key, index) => (
                <div
                  key={key}
                  className="flex items-start gap-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700"
                >
                  <div className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                    {index + 1}
                  </div>
                  <p>{t(key)}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-16">
          <div className="max-w-3xl">
            <h2 className="text-3xl font-semibold tracking-tight text-slate-950">
              {t("landing.capabilitiesTitle")}
            </h2>
            <p className="mt-4 text-base leading-7 text-slate-600">
              {t("landing.capabilitiesSubtitle")}
            </p>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {capabilities.map((capability) => (
              <article
                key={capability.title}
                className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
              >
                <div className={`inline-flex h-12 w-12 items-center justify-center rounded-2xl ${capability.accent}`}>
                  <capability.icon size={22} />
                </div>
                <h3 className="mt-5 text-lg font-semibold text-slate-900">
                  {capability.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-slate-600">
                  {capability.description}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-16 rounded-[2rem] border border-slate-200/80 bg-slate-900 px-6 py-8 text-white shadow-[0_24px_80px_rgba(15,23,42,0.14)] sm:px-8">
          <div className="max-w-3xl">
            <h2 className="text-3xl font-semibold tracking-tight">
              {t("landing.proofTitle")}
            </h2>
            <p className="mt-4 text-base leading-7 text-slate-300">
              {t("landing.proofSubtitle")}
            </p>
          </div>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {proofPoints.map((item) => (
              <article
                key={item.title}
                className="rounded-3xl border border-white/10 bg-white/5 p-5"
              >
                <item.icon size={20} className="text-indigo-300" />
                <h3 className="mt-4 text-lg font-semibold text-white">{item.title}</h3>
                <p className="mt-2 text-sm leading-7 text-slate-300">{item.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-16">
          <h2 className="text-3xl font-semibold tracking-tight text-slate-950">
            {t("landing.faqTitle")}
          </h2>
          <div className="mt-8 grid gap-4 lg:grid-cols-3">
            {FAQ_ITEMS.map((item) => (
              <article key={item.question} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900">
                  {t(item.question)}
                </h3>
                <p className="mt-3 text-sm leading-7 text-slate-600">
                  {t(item.answer)}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-16 rounded-[2rem] border border-slate-200 bg-white px-6 py-8 shadow-sm sm:px-8">
          <h2 className="text-3xl font-semibold tracking-tight text-slate-950">
            {t("landing.finalTitle")}
          </h2>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
            {t("landing.finalSubtitle")}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/workspace"
              className="inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-slate-800"
            >
              {t("landing.primaryCta")}
              <ArrowRight size={16} />
            </Link>
            <a
              href={GITHUB_REPO}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:border-slate-300 hover:text-slate-900"
            >
              {t("landing.secondaryCta")}
              <ExternalLink size={16} />
            </a>
          </div>
        </section>

        <SiteFooter />
      </main>
    </div>
  );
}

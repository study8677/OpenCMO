import {
  ArrowRight,
  ExternalLink,
  Github,
  MonitorPlay,
} from "lucide-react";
import { Link } from "react-router";
import { SiteFooter } from "../components/layout/SiteFooter";
import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SectionReveal } from "../components/marketing/SectionReveal";
import { BuiltInOpen } from "../components/marketing/BuiltInOpen";
import {
  PUBLIC_HOME_NAV,
  getContactPath,
  getServicesPath,
} from "../content/marketing";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { useI18n } from "../i18n";
import { getSeoLocaleFromLocale } from "../utils/publicRoutes";

const GITHUB_REPO_URL = "https://github.com/study8677/OpenCMO";
const CONTACT_EMAIL = "hello@aidcmo.com";

// Neutral signal lanes (kept from old landing — no B2B baggage).
// These describe what OpenCMO actually does, in plain language.
const SIGNAL_LANES = [
  "landing.boardStream1",
  "landing.boardStream2",
  "landing.boardStream3",
] as const;

const PIPELINE_STAGES = [
  "landing.stage1",
  "landing.stage2",
  "landing.stage3",
  "landing.stage4",
  "landing.stage5",
  "landing.stage6",
] as const;

const HERO_BADGES = [
  "landing.heroBadgeOpenSource",
  "landing.heroBadgeLicense",
  "landing.heroBadgeSelfHost",
  "landing.heroBadgeByok",
] as const;

const PATH_CARDS = [
  {
    title: "landing.pathPrivateTitle",
    body: "landing.pathPrivateDesc",
    cta: "landing.heroPrimaryCta",
    href: "/services",
    external: false,
  },
  {
    title: "landing.pathGithubTitle",
    body: "landing.pathGithubDesc",
    cta: "landing.heroSecondaryCta",
    href: GITHUB_REPO_URL,
    external: true,
  },
  {
    title: "landing.pathDeployedTitle",
    body: "landing.pathDeployedDesc",
    cta: "landing.workspaceCta",
    href: "/workspace",
    external: false,
  },
] as const;

export function LandingPage() {
  const { t, locale } = useI18n();
  const seoLocale = getSeoLocaleFromLocale(locale);

  usePublicPageMetadata({
    title: t("landing.metaTitle"),
    description: t("landing.metaDescription"),
    basePath: "/",
  });

  const getPathCardHref = (href: string) => {
    if (href === "/services") {
      return getServicesPath(seoLocale);
    }
    return href;
  };

  return (
    <div className="min-h-screen bg-[#08141f] text-white">
      <PublicSiteHeader items={PUBLIC_HOME_NAV} theme="dark" />

      <main className="overflow-hidden">
        {/* Hero ----------------------------------------------------- */}
        <section className="relative">
          <div className="mx-auto max-w-7xl px-4 pb-24 pt-20 text-center sm:pb-28 sm:pt-24 lg:px-8">
            <p className="text-sm font-semibold uppercase tracking-wider text-white/55">
              {t("landing.heroEyebrow")}
            </p>
            <h1 className="font-display mx-auto mt-6 max-w-5xl text-5xl font-semibold tracking-tight text-white sm:text-6xl lg:text-7xl">
              {t("landing.heroTitle")}
            </h1>
            <p className="mx-auto mt-7 max-w-3xl text-lg leading-8 text-white/70 sm:text-xl sm:leading-9">
              {t("landing.heroSubtitle")}
            </p>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              <Link
                to={getServicesPath(seoLocale)}
                className="inline-flex items-center gap-2 rounded-full bg-[#f7ecde] px-7 py-4 text-sm font-semibold text-[#082032] transition-colors hover:bg-white"
              >
                {t("landing.heroPrimaryCta")}
                <ArrowRight size={16} />
              </Link>
              <a
                href={GITHUB_REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/6 px-7 py-4 text-sm font-semibold text-white/90 transition-colors hover:border-white/25 hover:text-white"
              >
                <Github size={16} />
                {t("landing.heroSecondaryCta")}
                <ExternalLink size={14} />
              </a>
              <Link
                to="/workspace"
                className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/6 px-7 py-4 text-sm font-semibold text-white/90 transition-colors hover:border-white/25 hover:text-white"
              >
                <MonitorPlay size={16} />
                {t("landing.workspaceCta")}
                <ArrowRight size={14} />
              </Link>
            </div>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
              {HERO_BADGES.map((key) => (
                <span
                  key={key}
                  className="rounded-full border border-white/10 bg-white/4 px-3 py-1.5 text-xs font-semibold text-white/65"
                >
                  {t(key)}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* Built in the open --------------------------------------- */}
        <BuiltInOpen />

        {/* What OpenCMO does --------------------------------------- */}
        <section className="bg-[#08141f]">
          <div className="mx-auto max-w-7xl px-4 py-20 lg:px-8 lg:py-24">
            <SectionReveal>
              <div className="max-w-3xl">
                <p className="text-sm font-semibold uppercase tracking-wider text-white/55">
                  {t("landing.signalBoardEyebrow")}
                </p>
                <h2 className="font-display mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                  {t("landing.signalBoardTitle")}
                </h2>
                <p className="mt-4 text-base leading-7 text-white/70">
                  {t("landing.signalBoardSummary")}
                </p>
              </div>
            </SectionReveal>

            <div className="mt-10 grid gap-4 lg:grid-cols-3">
              {SIGNAL_LANES.map((key, idx) => (
                <SectionReveal key={key} delay={idx * 0.05}>
                  <div className="rounded-2xl border border-white/8 bg-white/4 p-6">
                    <p className="text-base leading-7 text-white/80">{t(key)}</p>
                  </div>
                </SectionReveal>
              ))}
            </div>
          </div>
        </section>

        {/* Pipeline ------------------------------------------------ */}
        <section className="border-y border-white/8 bg-[#06121d]">
          <div className="mx-auto max-w-7xl px-4 py-20 lg:px-8 lg:py-24">
            <SectionReveal>
              <p className="text-sm font-semibold uppercase tracking-wider text-white/55">
                {t("landing.boardStagesTitle")}
              </p>
              <h2 className="font-display mt-4 max-w-2xl text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                {t("landing.metricPipelineValue")} · {t("landing.metricChannelsValue")}
              </h2>
            </SectionReveal>

            <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {PIPELINE_STAGES.map((key, idx) => (
                <SectionReveal key={key} delay={idx * 0.04}>
                  <div className="flex items-start gap-3 rounded-xl border border-white/8 bg-white/3 px-5 py-4">
                    <span className="mt-0.5 inline-flex h-7 min-w-7 items-center justify-center rounded-full bg-white/8 text-xs font-semibold text-white/85">
                      {idx + 1}
                    </span>
                    <span className="text-sm font-semibold text-white/85">
                      {t(key)}
                    </span>
                  </div>
                </SectionReveal>
              ))}
            </div>
          </div>
        </section>

        {/* Three paths ---------------------------------------------- */}
        <section className="bg-[#08141f]">
          <div className="mx-auto max-w-7xl px-4 py-20 lg:px-8 lg:py-24">
            <SectionReveal>
              <div className="max-w-3xl">
                <p className="text-sm font-semibold uppercase tracking-wider text-white/55">
                  {t("landing.pathEyebrow")}
                </p>
                <h2 className="font-display mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                  {t("landing.pathTitle")}
                </h2>
                <p className="mt-4 text-base leading-7 text-white/70">
                  {t("landing.pathSubtitle")}
                </p>
              </div>
            </SectionReveal>

            <div className="mt-10 grid gap-4 lg:grid-cols-3">
              {PATH_CARDS.map((item, idx) => (
                <SectionReveal key={item.title} delay={idx * 0.05}>
                  <div className="flex h-full flex-col rounded-2xl border border-white/8 bg-white/4 p-6">
                    <h3 className="text-xl font-semibold text-white">{t(item.title)}</h3>
                    <p className="mt-3 flex-1 text-sm leading-6 text-white/66">{t(item.body)}</p>
                    {item.external ? (
                      <a
                        href={item.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-white transition-colors hover:text-[#f7ecde]"
                      >
                        {t(item.cta)}
                        <ExternalLink size={14} />
                      </a>
                    ) : (
                      <Link
                        to={getPathCardHref(item.href)}
                        className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-white transition-colors hover:text-[#f7ecde]"
                      >
                        {t(item.cta)}
                        <ArrowRight size={14} />
                      </Link>
                    )}
                  </div>
                </SectionReveal>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA ----------------------------------------------- */}
        <section className="bg-[#06121d]">
          <div className="mx-auto max-w-5xl px-4 py-20 text-center lg:px-8 lg:py-24">
            <SectionReveal>
              <h2 className="font-display text-3xl font-semibold tracking-tight text-white sm:text-4xl lg:text-5xl">
                {t("landing.heroPrimaryCta")}
              </h2>
              <p className="mx-auto mt-5 max-w-2xl text-base text-white/70">
                {t("landing.emailHeroHint")}
              </p>
              <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                <Link
                  to={getServicesPath(seoLocale)}
                  className="inline-flex items-center gap-2 rounded-full bg-[#f7ecde] px-7 py-4 text-sm font-semibold text-[#082032] transition-colors hover:bg-white"
                >
                  {t("landing.heroPrimaryCta")}
                  <ArrowRight size={16} />
                </Link>
                <Link
                  to={getContactPath(seoLocale)}
                  className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/6 px-7 py-4 text-sm font-semibold text-white/90 transition-colors hover:border-white/25 hover:text-white"
                >
                  {t("landing.contactCta")}
                </Link>
                <a
                  href={GITHUB_REPO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-white/65 transition-colors hover:text-white"
                >
                  {t("landing.heroSecondaryCta")}
                  <ExternalLink size={14} />
                </a>
                <Link
                  to="/workspace"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-white/65 transition-colors hover:text-white"
                >
                  {t("landing.workspaceCta")}
                  <ArrowRight size={14} />
                </Link>
              </div>
              <p className="mt-10 text-sm text-white/55">
                {t("landing.emailLabel")} ·{" "}
                <a
                  href={`mailto:${CONTACT_EMAIL}`}
                  className="text-white/85 underline-offset-4 hover:underline"
                >
                  {CONTACT_EMAIL}
                </a>
              </p>
            </SectionReveal>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}

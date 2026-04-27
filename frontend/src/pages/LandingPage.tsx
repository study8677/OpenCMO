import {
  ArrowRight,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  Database,
  Filter,
  MailCheck,
  Search,
  ShieldCheck,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { Link } from "react-router";
import { SiteFooter } from "../components/layout/SiteFooter";
import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SectionReveal } from "../components/marketing/SectionReveal";
import {
  PUBLIC_HOME_NAV,
  getB2BLeadsPath,
  getContactPath,
  getDataPolicyPath,
  getOpenSourcePath,
  getSampleDataPath,
  getSeoGeoPath,
} from "../content/marketing";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { useI18n } from "../i18n";
import type { TranslationKey } from "../i18n";
import { getSeoLocaleFromLocale } from "../utils/publicRoutes";

const GITHUB_REPO_URL = "https://github.com/study8677/OpenCMO";
const CONTACT_EMAIL = "hello@aidcmo.com";

const SERVICE_MODULES: Array<{
  icon: LucideIcon;
  title: TranslationKey;
  description: TranslationKey;
  href: (locale: "en" | "zh") => string;
  cta: TranslationKey;
}> = [
  {
    icon: Database,
    title: "landing.serviceLeadsTitle",
    description: "landing.serviceLeadsDesc",
    href: getB2BLeadsPath,
    cta: "landing.learnMoreCta",
  },
  {
    icon: MailCheck,
    title: "landing.serviceCleanTitle",
    description: "landing.serviceCleanDesc",
    href: getDataPolicyPath,
    cta: "landing.dataPolicyCta",
  },
  {
    icon: Search,
    title: "landing.serviceSeoGeoTitle",
    description: "landing.serviceSeoGeoDesc",
    href: getSeoGeoPath,
    cta: "landing.seoConsultCta",
  },
];

const FILTER_ITEMS = [
  "landing.filterCountry",
  "landing.filterRegion",
  "landing.filterIndustry",
  "landing.filterRole",
  "landing.filterScale",
  "landing.filterDomain",
] as TranslationKey[];

const FIELD_ITEMS = [
  "landing.fieldCompany",
  "landing.fieldWebsite",
  "landing.fieldContact",
  "landing.fieldTitle",
  "landing.fieldEmail",
  "landing.fieldLinkedin",
  "landing.fieldRegion",
  "landing.fieldValidation",
] as TranslationKey[];

const COMPLIANCE_ITEMS = [
  "landing.complianceB2B",
  "landing.compliancePublic",
  "landing.complianceRemoval",
  "landing.complianceNoSpam",
  "landing.complianceNoGuarantee",
] as TranslationKey[];

const OPENCMO_POINTS = [
  "landing.openCmoPointSeo",
  "landing.openCmoPointGeo",
  "landing.openCmoPointSerp",
  "landing.openCmoPointNarrative",
] as TranslationKey[];

function DevicePreview() {
  const { t } = useI18n();

  return (
    <div className="mx-auto mt-14 max-w-6xl px-2">
      <div className="relative overflow-hidden rounded-[2.25rem] bg-[#1d1d1f] px-4 pt-8 shadow-[0_40px_120px_rgba(0,0,0,0.22)] sm:px-8 lg:px-10">
        <div className="mx-auto grid max-w-5xl gap-7 lg:grid-cols-[340px_minmax(0,1fr)] lg:items-end">
          <div className="mx-auto w-full max-w-[310px] rounded-[2.15rem] border-[10px] border-black bg-black p-1 shadow-[0_28px_80px_rgba(0,0,0,0.35)]">
            <div className="overflow-hidden rounded-[1.55rem] bg-[#f5f5f7]">
              <div className="mx-auto mt-3 h-5 w-24 rounded-full bg-black" />
              <div className="p-5">
                <p className="text-xs font-semibold uppercase text-slate-500">
                  {t("landing.phoneLabel")}
                </p>
                <h2 className="mt-3 text-3xl font-semibold tracking-tight text-[#1d1d1f]">
                  {t("landing.phoneTitle")}
                </h2>
                <div className="mt-5 space-y-2">
                  {FILTER_ITEMS.slice(0, 4).map((key) => (
                    <div key={key} className="flex items-center justify-between rounded-lg bg-white px-3 py-3">
                      <span className="text-sm font-medium text-slate-700">{t(key)}</span>
                      <CheckCircle2 size={16} className="text-emerald-600" />
                    </div>
                  ))}
                </div>
                <div className="mt-5 rounded-lg bg-[#1d1d1f] px-4 py-4 text-white">
                  <p className="text-xs uppercase text-white/45">{t("landing.phoneStatusLabel")}</p>
                  <p className="mt-2 text-2xl font-semibold">{t("landing.phoneStatusValue")}</p>
                  <p className="mt-2 text-xs leading-5 text-white/58">{t("landing.phoneStatusDesc")}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="pb-8">
            <div className="rounded-lg bg-white p-5 shadow-[0_24px_80px_rgba(0,0,0,0.18)]">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
                <div>
                  <p className="text-xs font-semibold uppercase text-slate-400">{t("landing.desktopLabel")}</p>
                  <h2 className="mt-2 text-2xl font-semibold text-[#1d1d1f]">{t("landing.desktopTitle")}</h2>
                </div>
                <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
                  {t("landing.desktopBadge")}
                </span>
              </div>
              <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
                <div className="grid grid-cols-[1fr_1fr_1fr] bg-slate-50 px-4 py-3 text-xs font-semibold uppercase text-slate-400">
                  <span>{t("landing.tableHeadAccount")}</span>
                  <span>{t("landing.tableHeadContact")}</span>
                  <span>{t("landing.tableHeadStatus")}</span>
                </div>
                {["landing.tableRow1", "landing.tableRow2", "landing.tableRow3"].map((key) => (
                  <div key={key} className="grid grid-cols-[1fr_1fr_1fr] border-t border-slate-200 px-4 py-4 text-sm text-slate-700">
                    <span>{t(key as TranslationKey)}</span>
                    <span>{t("landing.tableRole")}</span>
                    <span className="font-semibold text-emerald-700">{t("landing.tableVerified")}</span>
                  </div>
                ))}
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                {["landing.desktopMetric1", "landing.desktopMetric2", "landing.desktopMetric3"].map((key) => (
                  <div key={key} className="rounded-lg bg-[#f5f5f7] px-4 py-4">
                    <p className="text-sm font-semibold text-[#1d1d1f]">{t(key as TranslationKey)}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function LandingPage() {
  const { t, locale } = useI18n();
  const seoLocale = getSeoLocaleFromLocale(locale);

  usePublicPageMetadata({
    title: t("landing.metaTitle"),
    description: t("landing.metaDescription"),
    basePath: "/",
  });

  return (
    <div className="min-h-screen bg-[#f5f5f7] text-[#1d1d1f]">
      <PublicSiteHeader items={PUBLIC_HOME_NAV} theme="light" />

      <main className="overflow-hidden">
        <section className="bg-[#f5f5f7]">
          <div className="mx-auto max-w-7xl px-4 pb-20 pt-16 text-center sm:pb-24 sm:pt-20 lg:px-8">
            <p className="text-sm font-semibold uppercase text-[#6e6e73]">{t("landing.heroEyebrow")}</p>
            <h1 className="font-display mx-auto mt-5 max-w-5xl text-5xl font-semibold tracking-tight text-[#1d1d1f] sm:text-7xl lg:text-8xl">
              {t("landing.heroTitle")}
            </h1>
            <p className="mx-auto mt-6 max-w-3xl text-xl leading-8 text-[#6e6e73] sm:text-2xl sm:leading-9">
              {t("landing.heroSubtitle")}
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="inline-flex items-center gap-2 rounded-lg bg-[#0071e3] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#0077ed]"
              >
                {CONTACT_EMAIL}
                <ArrowRight size={16} />
              </a>
              <Link
                to={getSampleDataPath(seoLocale)}
                className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3 text-sm font-semibold text-[#0071e3] transition-colors hover:bg-slate-50"
              >
                {t("landing.sampleDataCta")}
              </Link>
              <Link
                to={getSeoGeoPath(seoLocale)}
                className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3 text-sm font-semibold text-[#0071e3] transition-colors hover:bg-slate-50"
              >
                {t("landing.seoConsultCta")}
                <ArrowUpRight size={16} />
              </Link>
            </div>
            <a
              href={`mailto:${CONTACT_EMAIL}`}
              className="mx-auto mt-8 block max-w-3xl rounded-[1.8rem] bg-white px-6 py-7 text-center shadow-[0_24px_80px_rgba(0,0,0,0.08)] transition-transform duration-300 hover:-translate-y-1"
            >
              <p className="text-sm font-semibold uppercase text-[#6e6e73]">{t("landing.emailLabel")}</p>
              <p className="mt-3 break-words text-4xl font-semibold tracking-tight text-[#0071e3] sm:text-6xl">
                {CONTACT_EMAIL}
              </p>
              <p className="mt-4 text-base leading-7 text-[#6e6e73]">{t("landing.emailHeroHint")}</p>
            </a>
            <DevicePreview />
          </div>
        </section>

        <section id="services" className="bg-white">
          <div className="mx-auto max-w-7xl px-4 py-16 lg:px-8 lg:py-24">
            <SectionReveal>
              <div className="text-center">
                <p className="text-sm font-semibold uppercase text-[#6e6e73]">{t("landing.servicesEyebrow")}</p>
                <h2 className="font-display mx-auto mt-4 max-w-4xl text-4xl font-semibold tracking-tight sm:text-6xl">
                  {t("landing.servicesTitle")}
                </h2>
                <p className="mx-auto mt-5 max-w-3xl text-lg leading-8 text-[#6e6e73]">
                  {t("landing.servicesSubtitle")}
                </p>
              </div>
            </SectionReveal>

            <div className="mt-12 grid gap-4 lg:grid-cols-3">
              {SERVICE_MODULES.map((service, index) => {
                const Icon = service.icon;
                return (
                  <SectionReveal key={service.title} delay={index * 0.05}>
                    <Link
                      to={service.href(seoLocale)}
                      className="group block h-full rounded-lg bg-[#f5f5f7] p-7 transition-transform duration-300 hover:-translate-y-1"
                    >
                      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-[#0071e3]">
                        <Icon size={19} />
                      </div>
                      <h3 className="mt-8 text-2xl font-semibold tracking-tight">{t(service.title)}</h3>
                      <p className="mt-4 text-base leading-8 text-[#6e6e73]">{t(service.description)}</p>
                      <span className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[#0071e3]">
                        {t(service.cta)}
                        <ArrowUpRight size={15} className="transition-transform group-hover:translate-x-0.5" />
                      </span>
                    </Link>
                  </SectionReveal>
                );
              })}
            </div>
          </div>
        </section>

        <section className="bg-[#1d1d1f] text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-4 py-16 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:px-8 lg:py-24 lg:items-center">
            <SectionReveal>
              <p className="text-sm font-semibold uppercase text-white/50">{t("landing.leadsEyebrow")}</p>
              <h2 className="font-display mt-4 text-4xl font-semibold tracking-tight sm:text-6xl">
                {t("landing.leadsTitle")}
              </h2>
              <p className="mt-5 max-w-2xl text-lg leading-8 text-white/64">{t("landing.leadsSubtitle")}</p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  to={getB2BLeadsPath(seoLocale)}
                  className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3 text-sm font-semibold text-[#1d1d1f] transition-colors hover:bg-[#f5f5f7]"
                >
                  {t("landing.learnMoreCta")}
                  <ArrowRight size={16} />
                </Link>
                <Link
                  to={getSampleDataPath(seoLocale)}
                  className="inline-flex items-center gap-2 rounded-lg border border-white/18 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/8"
                >
                  {t("landing.sampleDataCta")}
                </Link>
              </div>
            </SectionReveal>

            <SectionReveal delay={0.08}>
              <div className="rounded-lg bg-white p-5 text-[#1d1d1f]">
                <div className="grid gap-3 sm:grid-cols-2">
                  {FILTER_ITEMS.map((key) => (
                    <div key={key} className="flex items-center gap-3 rounded-lg bg-[#f5f5f7] px-4 py-4">
                      <Filter size={16} className="text-[#0071e3]" />
                      <span className="text-sm font-semibold">{t(key)}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-5 border-t border-slate-200 pt-5">
                  <p className="text-sm font-semibold uppercase text-[#6e6e73]">{t("landing.fieldsLabel")}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {FIELD_ITEMS.map((key) => (
                      <span key={key} className="rounded-full bg-[#f5f5f7] px-3 py-2 text-xs font-semibold text-[#424245]">
                        {t(key)}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </SectionReveal>
          </div>
        </section>

        <section className="bg-[#f5f5f7]">
          <div className="mx-auto grid max-w-7xl gap-8 px-4 py-16 lg:grid-cols-2 lg:px-8 lg:py-24">
            <SectionReveal>
              <div className="h-full rounded-lg bg-white p-8">
                <Search size={28} className="text-[#0071e3]" />
                <h2 className="font-display mt-8 text-4xl font-semibold tracking-tight sm:text-5xl">
                  {t("landing.seoBlockTitle")}
                </h2>
                <p className="mt-5 text-lg leading-8 text-[#6e6e73]">{t("landing.seoBlockBody")}</p>
                <Link
                  to={getSeoGeoPath(seoLocale)}
                  className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-[#0071e3]"
                >
                  {t("landing.seoConsultCta")}
                  <ArrowUpRight size={15} />
                </Link>
              </div>
            </SectionReveal>

            <SectionReveal delay={0.08}>
              <div className="h-full rounded-lg bg-white p-8">
                <Bot size={28} className="text-[#0071e3]" />
                <h2 className="font-display mt-8 text-4xl font-semibold tracking-tight sm:text-5xl">
                  {t("landing.geoBlockTitle")}
                </h2>
                <p className="mt-5 text-lg leading-8 text-[#6e6e73]">{t("landing.geoBlockBody")}</p>
                <div className="mt-7 grid gap-3">
                  {["landing.geoPoint1", "landing.geoPoint2", "landing.geoPoint3"].map((key) => (
                    <div key={key} className="flex items-start gap-3">
                      <CheckCircle2 size={17} className="mt-1 shrink-0 text-emerald-600" />
                      <span className="text-sm leading-6 text-[#424245]">{t(key as TranslationKey)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </SectionReveal>
          </div>
        </section>

        <section className="bg-white">
          <div className="mx-auto grid max-w-7xl gap-10 px-4 py-16 lg:grid-cols-[minmax(0,1fr)_420px] lg:px-8 lg:py-24 lg:items-center">
            <SectionReveal>
              <p className="text-sm font-semibold uppercase text-[#6e6e73]">{t("landing.openCmoEyebrow")}</p>
              <h2 className="font-display mt-4 text-4xl font-semibold tracking-tight sm:text-6xl">
                {t("landing.openCmoTitle")}
              </h2>
              <p className="mt-5 max-w-3xl text-lg leading-8 text-[#6e6e73]">{t("landing.openCmoSubtitle")}</p>
              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href={GITHUB_REPO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-lg bg-[#1d1d1f] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-black"
                >
                  {t("landing.githubCta")}
                  <ArrowUpRight size={16} />
                </a>
                <Link
                  to={getOpenSourcePath(seoLocale)}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#f5f5f7] px-5 py-3 text-sm font-semibold text-[#0071e3] transition-colors hover:bg-slate-100"
                >
                  {t("landing.openSourceCta")}
                  <ArrowRight size={16} />
                </Link>
              </div>
            </SectionReveal>

            <SectionReveal delay={0.08}>
              <div className="rounded-lg bg-[#f5f5f7] p-6">
                {OPENCMO_POINTS.map((key, index) => (
                  <div key={key} className="flex gap-4 border-b border-slate-200 py-4 last:border-b-0">
                    <span className="font-mono text-sm text-[#6e6e73]">{`${index + 1}`.padStart(2, "0")}</span>
                    <p className="text-base leading-7 text-[#424245]">{t(key)}</p>
                  </div>
                ))}
              </div>
            </SectionReveal>
          </div>
        </section>

        <section className="bg-[#f5f5f7]">
          <div className="mx-auto max-w-7xl px-4 py-16 lg:px-8 lg:py-24">
            <SectionReveal>
              <div className="text-center">
                <ShieldCheck size={28} className="mx-auto text-[#0071e3]" />
                <h2 className="font-display mx-auto mt-5 max-w-4xl text-4xl font-semibold tracking-tight sm:text-6xl">
                  {t("landing.complianceTitle")}
                </h2>
                <p className="mx-auto mt-5 max-w-3xl text-lg leading-8 text-[#6e6e73]">
                  {t("landing.complianceSubtitle")}
                </p>
              </div>
            </SectionReveal>
            <div className="mx-auto mt-10 grid max-w-5xl gap-3">
              {COMPLIANCE_ITEMS.map((key) => (
                <SectionReveal key={key}>
                  <div className="flex items-start gap-3 rounded-lg bg-white px-5 py-4">
                    <CheckCircle2 size={17} className="mt-1 shrink-0 text-emerald-600" />
                    <p className="text-sm leading-6 text-[#424245]">{t(key)}</p>
                  </div>
                </SectionReveal>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-white">
          <div className="mx-auto max-w-7xl px-4 py-16 text-center lg:px-8 lg:py-24">
            <SectionReveal>
              <Sparkles size={30} className="mx-auto text-[#0071e3]" />
              <h2 className="font-display mx-auto mt-5 max-w-4xl text-4xl font-semibold tracking-tight sm:text-6xl">
                {t("landing.finalTitle")}
              </h2>
              <p className="mx-auto mt-5 max-w-3xl text-lg leading-8 text-[#6e6e73]">{t("landing.finalSubtitle")}</p>
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="mx-auto mt-8 block w-fit rounded-[1.4rem] bg-[#f5f5f7] px-8 py-6 text-left transition-colors hover:bg-slate-100"
              >
                <p className="text-sm font-semibold uppercase text-[#6e6e73]">{t("landing.emailLabel")}</p>
                <p className="mt-2 text-3xl font-semibold tracking-tight text-[#0071e3] sm:text-5xl">
                  {CONTACT_EMAIL}
                </p>
              </a>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <a
                  href={`mailto:${CONTACT_EMAIL}`}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#0071e3] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#0077ed]"
                >
                  {t("landing.emailCta")}
                  <ArrowRight size={16} />
                </a>
                <Link
                  to={getSampleDataPath(seoLocale)}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#f5f5f7] px-5 py-3 text-sm font-semibold text-[#0071e3] transition-colors hover:bg-slate-100"
                >
                  {t("landing.sampleDataCta")}
                </Link>
                <Link
                  to={getContactPath(seoLocale)}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#f5f5f7] px-5 py-3 text-sm font-semibold text-[#0071e3] transition-colors hover:bg-slate-100"
                >
                  {t("landing.contactCta")}
                  <ArrowUpRight size={16} />
                </Link>
              </div>
            </SectionReveal>
          </div>
        </section>

        <div className="mx-auto max-w-7xl px-4 pb-12 lg:px-8">
          <SiteFooter variant="public" />
        </div>
      </main>
    </div>
  );
}

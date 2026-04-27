import {
  ArrowRight,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  Database,
  FileText,
  Filter,
  GitBranch,
  Globe,
  MailCheck,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
  type LucideIcon,
} from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";
import { SiteFooter } from "../components/layout/SiteFooter";
import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SectionReveal } from "../components/marketing/SectionReveal";
import { PUBLIC_HOME_NAV } from "../content/marketing";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { useI18n } from "../i18n";
import type { TranslationKey } from "../i18n";
import { getLocalizedPublicPath, getSeoLocaleFromLocale } from "../utils/publicRoutes";

const GITHUB_REPO_URL = "https://github.com/study8677/OpenCMO";

export type PublicServicePageKind =
  | "b2b-leads"
  | "seo-geo"
  | "open-source"
  | "sample-data"
  | "contact"
  | "data-policy";

type PageSection = {
  icon: LucideIcon;
  title: TranslationKey;
  description: TranslationKey;
};

type ServicePageContent = {
  path: string;
  metaTitle: TranslationKey;
  metaDescription: TranslationKey;
  eyebrow: TranslationKey;
  title: TranslationKey;
  subtitle: TranslationKey;
  primaryCta: TranslationKey;
  primaryHref: string;
  secondaryCta: TranslationKey;
  secondaryHref: string;
  highlights: TranslationKey[];
  sectionEyebrow: TranslationKey;
  sectionTitle: TranslationKey;
  sectionSubtitle: TranslationKey;
  sections: PageSection[];
  detailTitle: TranslationKey;
  detailSubtitle: TranslationKey;
  details: TranslationKey[];
  fieldTitle: TranslationKey;
  fields: TranslationKey[];
  noteTitle: TranslationKey;
  noteBody: TranslationKey;
  finalTitle: TranslationKey;
  finalSubtitle: TranslationKey;
};

const CONTACT_EMAIL = "hello@aidcmo.com";

const PAGE_CONTENT: Record<PublicServicePageKind, ServicePageContent> = {
  "b2b-leads": {
    path: "/b2b-leads",
    metaTitle: "service.b2b.metaTitle",
    metaDescription: "service.b2b.metaDescription",
    eyebrow: "service.b2b.eyebrow",
    title: "service.b2b.title",
    subtitle: "service.b2b.subtitle",
    primaryCta: "landing.sampleDataCta",
    primaryHref: "/sample-data",
    secondaryCta: "landing.contactCta",
    secondaryHref: "/contact",
    highlights: ["service.b2b.highlight1", "service.b2b.highlight2", "service.b2b.highlight3"],
    sectionEyebrow: "service.b2b.sectionEyebrow",
    sectionTitle: "service.b2b.sectionTitle",
    sectionSubtitle: "service.b2b.sectionSubtitle",
    sections: [
      { icon: Globe, title: "service.b2b.countryTitle", description: "service.b2b.countryDesc" },
      { icon: Filter, title: "service.b2b.industryTitle", description: "service.b2b.industryDesc" },
      { icon: Users, title: "service.b2b.roleTitle", description: "service.b2b.roleDesc" },
      { icon: Database, title: "service.b2b.scaleTitle", description: "service.b2b.scaleDesc" },
      { icon: MailCheck, title: "service.b2b.validationTitle", description: "service.b2b.validationDesc" },
      { icon: ShieldCheck, title: "service.b2b.riskTitle", description: "service.b2b.riskDesc" },
    ],
    detailTitle: "service.b2b.detailTitle",
    detailSubtitle: "service.b2b.detailSubtitle",
    details: [
      "service.b2b.detail1",
      "service.b2b.detail2",
      "service.b2b.detail3",
      "service.b2b.detail4",
      "service.b2b.detail5",
    ],
    fieldTitle: "service.b2b.fieldTitle",
    fields: [
      "service.b2b.field1",
      "service.b2b.field2",
      "service.b2b.field3",
      "service.b2b.field4",
      "service.b2b.field5",
      "service.b2b.field6",
      "service.b2b.field7",
      "service.b2b.field8",
    ],
    noteTitle: "service.b2b.noteTitle",
    noteBody: "service.b2b.noteBody",
    finalTitle: "service.b2b.finalTitle",
    finalSubtitle: "service.b2b.finalSubtitle",
  },
  "seo-geo": {
    path: "/seo-geo",
    metaTitle: "service.seoGeo.metaTitle",
    metaDescription: "service.seoGeo.metaDescription",
    eyebrow: "service.seoGeo.eyebrow",
    title: "service.seoGeo.title",
    subtitle: "service.seoGeo.subtitle",
    primaryCta: "landing.seoConsultCta",
    primaryHref: "/contact",
    secondaryCta: "landing.openSourceCta",
    secondaryHref: "/open-source",
    highlights: ["service.seoGeo.highlight1", "service.seoGeo.highlight2", "service.seoGeo.highlight3"],
    sectionEyebrow: "service.seoGeo.sectionEyebrow",
    sectionTitle: "service.seoGeo.sectionTitle",
    sectionSubtitle: "service.seoGeo.sectionSubtitle",
    sections: [
      { icon: Search, title: "service.seoGeo.technicalTitle", description: "service.seoGeo.technicalDesc" },
      { icon: FileText, title: "service.seoGeo.contentTitle", description: "service.seoGeo.contentDesc" },
      { icon: Bot, title: "service.seoGeo.geoTitle", description: "service.seoGeo.geoDesc" },
      { icon: Sparkles, title: "service.seoGeo.entityTitle", description: "service.seoGeo.entityDesc" },
      { icon: Globe, title: "service.seoGeo.serpTitle", description: "service.seoGeo.serpDesc" },
      { icon: CheckCircle2, title: "service.seoGeo.reportTitle", description: "service.seoGeo.reportDesc" },
    ],
    detailTitle: "service.seoGeo.detailTitle",
    detailSubtitle: "service.seoGeo.detailSubtitle",
    details: [
      "service.seoGeo.detail1",
      "service.seoGeo.detail2",
      "service.seoGeo.detail3",
      "service.seoGeo.detail4",
      "service.seoGeo.detail5",
    ],
    fieldTitle: "service.seoGeo.fieldTitle",
    fields: [
      "service.seoGeo.field1",
      "service.seoGeo.field2",
      "service.seoGeo.field3",
      "service.seoGeo.field4",
      "service.seoGeo.field5",
      "service.seoGeo.field6",
    ],
    noteTitle: "service.seoGeo.noteTitle",
    noteBody: "service.seoGeo.noteBody",
    finalTitle: "service.seoGeo.finalTitle",
    finalSubtitle: "service.seoGeo.finalSubtitle",
  },
  "open-source": {
    path: "/open-source",
    metaTitle: "service.openSource.metaTitle",
    metaDescription: "service.openSource.metaDescription",
    eyebrow: "service.openSource.eyebrow",
    title: "service.openSource.title",
    subtitle: "service.openSource.subtitle",
    primaryCta: "service.openSource.repoCta",
    primaryHref: GITHUB_REPO_URL,
    secondaryCta: "landing.seoConsultCta",
    secondaryHref: "/seo-geo",
    highlights: ["service.openSource.highlight1", "service.openSource.highlight2", "service.openSource.highlight3"],
    sectionEyebrow: "service.openSource.sectionEyebrow",
    sectionTitle: "service.openSource.sectionTitle",
    sectionSubtitle: "service.openSource.sectionSubtitle",
    sections: [
      { icon: Search, title: "service.openSource.seoTitle", description: "service.openSource.seoDesc" },
      { icon: Bot, title: "service.openSource.geoTitle", description: "service.openSource.geoDesc" },
      { icon: Globe, title: "service.openSource.serpTitle", description: "service.openSource.serpDesc" },
      { icon: Users, title: "service.openSource.communityTitle", description: "service.openSource.communityDesc" },
      { icon: GitBranch, title: "service.openSource.methodTitle", description: "service.openSource.methodDesc" },
      { icon: ShieldCheck, title: "service.openSource.proofTitle", description: "service.openSource.proofDesc" },
    ],
    detailTitle: "service.openSource.detailTitle",
    detailSubtitle: "service.openSource.detailSubtitle",
    details: [
      "service.openSource.detail1",
      "service.openSource.detail2",
      "service.openSource.detail3",
      "service.openSource.detail4",
    ],
    fieldTitle: "service.openSource.fieldTitle",
    fields: [
      "service.openSource.field1",
      "service.openSource.field2",
      "service.openSource.field3",
      "service.openSource.field4",
    ],
    noteTitle: "service.openSource.noteTitle",
    noteBody: "service.openSource.noteBody",
    finalTitle: "service.openSource.finalTitle",
    finalSubtitle: "service.openSource.finalSubtitle",
  },
  "sample-data": {
    path: "/sample-data",
    metaTitle: "service.sample.metaTitle",
    metaDescription: "service.sample.metaDescription",
    eyebrow: "service.sample.eyebrow",
    title: "service.sample.title",
    subtitle: "service.sample.subtitle",
    primaryCta: "landing.contactCta",
    primaryHref: "/contact",
    secondaryCta: "landing.dataPolicyCta",
    secondaryHref: "/data-policy",
    highlights: ["service.sample.highlight1", "service.sample.highlight2", "service.sample.highlight3"],
    sectionEyebrow: "service.sample.sectionEyebrow",
    sectionTitle: "service.sample.sectionTitle",
    sectionSubtitle: "service.sample.sectionSubtitle",
    sections: [
      { icon: Globe, title: "service.sample.countryTitle", description: "service.sample.countryDesc" },
      { icon: Filter, title: "service.sample.segmentTitle", description: "service.sample.segmentDesc" },
      { icon: Users, title: "service.sample.personaTitle", description: "service.sample.personaDesc" },
      { icon: Database, title: "service.sample.volumeTitle", description: "service.sample.volumeDesc" },
      { icon: MailCheck, title: "service.sample.validationTitle", description: "service.sample.validationDesc" },
      { icon: ShieldCheck, title: "service.sample.useTitle", description: "service.sample.useDesc" },
    ],
    detailTitle: "service.sample.detailTitle",
    detailSubtitle: "service.sample.detailSubtitle",
    details: [
      "service.sample.detail1",
      "service.sample.detail2",
      "service.sample.detail3",
      "service.sample.detail4",
    ],
    fieldTitle: "service.sample.fieldTitle",
    fields: [
      "service.sample.field1",
      "service.sample.field2",
      "service.sample.field3",
      "service.sample.field4",
    ],
    noteTitle: "service.sample.noteTitle",
    noteBody: "service.sample.noteBody",
    finalTitle: "service.sample.finalTitle",
    finalSubtitle: "service.sample.finalSubtitle",
  },
  contact: {
    path: "/contact",
    metaTitle: "service.contact.metaTitle",
    metaDescription: "service.contact.metaDescription",
    eyebrow: "service.contact.eyebrow",
    title: "service.contact.title",
    subtitle: "service.contact.subtitle",
    primaryCta: "landing.emailCta",
    primaryHref: `mailto:${CONTACT_EMAIL}`,
    secondaryCta: "landing.seoConsultCta",
    secondaryHref: "/seo-geo",
    highlights: ["service.contact.highlight1", "service.contact.highlight2", "service.contact.highlight3"],
    sectionEyebrow: "service.contact.sectionEyebrow",
    sectionTitle: "service.contact.sectionTitle",
    sectionSubtitle: "service.contact.sectionSubtitle",
    sections: [
      { icon: Database, title: "service.contact.leadsTitle", description: "service.contact.leadsDesc" },
      { icon: Search, title: "service.contact.seoTitle", description: "service.contact.seoDesc" },
      { icon: Bot, title: "service.contact.geoTitle", description: "service.contact.geoDesc" },
      { icon: ShieldCheck, title: "service.contact.policyTitle", description: "service.contact.policyDesc" },
    ],
    detailTitle: "service.contact.detailTitle",
    detailSubtitle: "service.contact.detailSubtitle",
    details: [
      "service.contact.detail1",
      "service.contact.detail2",
      "service.contact.detail3",
      "service.contact.detail4",
    ],
    fieldTitle: "service.contact.fieldTitle",
    fields: [
      "service.contact.field1",
      "service.contact.field2",
      "service.contact.field3",
      "service.contact.field4",
    ],
    noteTitle: "service.contact.noteTitle",
    noteBody: "service.contact.noteBody",
    finalTitle: "service.contact.finalTitle",
    finalSubtitle: "service.contact.finalSubtitle",
  },
  "data-policy": {
    path: "/data-policy",
    metaTitle: "service.policy.metaTitle",
    metaDescription: "service.policy.metaDescription",
    eyebrow: "service.policy.eyebrow",
    title: "service.policy.title",
    subtitle: "service.policy.subtitle",
    primaryCta: "landing.sampleDataCta",
    primaryHref: "/sample-data",
    secondaryCta: "landing.contactCta",
    secondaryHref: "/contact",
    highlights: ["service.policy.highlight1", "service.policy.highlight2", "service.policy.highlight3"],
    sectionEyebrow: "service.policy.sectionEyebrow",
    sectionTitle: "service.policy.sectionTitle",
    sectionSubtitle: "service.policy.sectionSubtitle",
    sections: [
      { icon: ShieldCheck, title: "service.policy.b2bTitle", description: "service.policy.b2bDesc" },
      { icon: Globe, title: "service.policy.sourceTitle", description: "service.policy.sourceDesc" },
      { icon: MailCheck, title: "service.policy.validationTitle", description: "service.policy.validationDesc" },
      { icon: CheckCircle2, title: "service.policy.removalTitle", description: "service.policy.removalDesc" },
      { icon: FileText, title: "service.policy.useTitle", description: "service.policy.useDesc" },
      { icon: Sparkles, title: "service.policy.limitTitle", description: "service.policy.limitDesc" },
    ],
    detailTitle: "service.policy.detailTitle",
    detailSubtitle: "service.policy.detailSubtitle",
    details: [
      "service.policy.detail1",
      "service.policy.detail2",
      "service.policy.detail3",
      "service.policy.detail4",
      "service.policy.detail5",
    ],
    fieldTitle: "service.policy.fieldTitle",
    fields: [
      "service.policy.field1",
      "service.policy.field2",
      "service.policy.field3",
      "service.policy.field4",
      "service.policy.field5",
    ],
    noteTitle: "service.policy.noteTitle",
    noteBody: "service.policy.noteBody",
    finalTitle: "service.policy.finalTitle",
    finalSubtitle: "service.policy.finalSubtitle",
  },
};

function ActionLink({
  href,
  children,
  variant = "primary",
}: {
  href: string;
  children: ReactNode;
  variant?: "primary" | "secondary";
}) {
  const { locale } = useI18n();
  const seoLocale = getSeoLocaleFromLocale(locale);
  const className =
    variant === "primary"
      ? "inline-flex items-center gap-2 rounded-lg bg-[#0071e3] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#0077ed]"
      : "inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3 text-sm font-semibold text-[#0071e3] transition-colors hover:bg-slate-50";

  if (href.startsWith("http") || href.startsWith("mailto:")) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
        {children}
        <ArrowUpRight size={16} />
      </a>
    );
  }

  return (
    <Link to={getLocalizedPublicPath(href, seoLocale)} className={className}>
      {children}
      {variant === "primary" ? <ArrowRight size={16} /> : <ArrowUpRight size={16} />}
    </Link>
  );
}

export function PublicServicePage({ kind }: { kind: PublicServicePageKind }) {
  const { t } = useI18n();
  const content = PAGE_CONTENT[kind];

  usePublicPageMetadata({
    title: t(content.metaTitle),
    description: t(content.metaDescription),
    basePath: content.path,
  });

  return (
    <div className="min-h-screen bg-[#f5f5f7] text-[#1d1d1f]">
      <PublicSiteHeader items={PUBLIC_HOME_NAV} theme="light" />

      <main className="pb-16">
        <section className="bg-[#f5f5f7]">
          <div className="mx-auto grid max-w-7xl gap-10 px-4 py-16 lg:grid-cols-[minmax(0,1fr)_420px] lg:px-8 lg:py-24">
            <div className="max-w-4xl">
              <p className="text-sm font-semibold uppercase text-[#6e6e73]">{t(content.eyebrow)}</p>
              <h1 className="font-display mt-5 text-5xl font-semibold tracking-tight text-[#1d1d1f] sm:text-7xl sm:leading-none">
                {t(content.title)}
              </h1>
              <p className="mt-6 max-w-3xl text-xl leading-9 text-[#6e6e73]">{t(content.subtitle)}</p>
              {kind === "contact" && (
                <a
                  href={`mailto:${CONTACT_EMAIL}`}
                  className="mt-8 block rounded-[1.8rem] bg-white px-6 py-8 shadow-[0_24px_80px_rgba(0,0,0,0.08)] transition-transform duration-300 hover:-translate-y-1"
                >
                  <p className="text-sm font-semibold uppercase text-[#6e6e73]">
                    {t("service.contact.emailLabel")}
                  </p>
                  <p className="mt-3 break-words text-4xl font-semibold tracking-tight text-[#0071e3] sm:text-6xl">
                    {CONTACT_EMAIL}
                  </p>
                  <p className="mt-4 text-base leading-7 text-[#6e6e73]">
                    {t("service.contact.emailHint")}
                  </p>
                </a>
              )}
              <div className="mt-8 flex flex-wrap gap-3">
                <ActionLink href={content.primaryHref}>{t(content.primaryCta)}</ActionLink>
                <ActionLink href={content.secondaryHref} variant="secondary">
                  {t(content.secondaryCta)}
                </ActionLink>
              </div>
            </div>

            <div className="grid gap-3 self-end">
              {kind === "contact" && (
                <a
                  href={`mailto:${CONTACT_EMAIL}`}
                  className="rounded-[1.4rem] bg-[#0071e3] px-6 py-7 text-white transition-colors hover:bg-[#0077ed]"
                >
                  <p className="text-sm font-semibold uppercase text-white/65">
                    {t("service.contact.emailLabel")}
                  </p>
                  <p className="mt-3 break-words text-3xl font-semibold tracking-tight sm:text-4xl">
                    {CONTACT_EMAIL}
                  </p>
                  <p className="mt-4 text-sm leading-6 text-white/72">
                    {t("service.contact.emailHint")}
                  </p>
                </a>
              )}
              {content.highlights.map((key, index) => (
                <div key={key} className="rounded-lg bg-white px-4 py-4">
                  <p className="text-xs font-semibold text-[#6e6e73]">0{index + 1}</p>
                  <p className="mt-2 text-sm leading-6 text-[#424245]">{t(key)}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 py-16 lg:px-8 lg:py-20">
          <SectionReveal>
            <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)] lg:items-end">
              <div>
                <p className="text-sm font-semibold uppercase text-[#6e6e73]">
                  {t(content.sectionEyebrow)}
                </p>
                <h2 className="font-display mt-3 text-4xl font-semibold tracking-tight text-[#1d1d1f] sm:text-6xl">
                  {t(content.sectionTitle)}
                </h2>
              </div>
              <p className="max-w-3xl text-lg leading-8 text-[#6e6e73]">
                {t(content.sectionSubtitle)}
              </p>
            </div>
          </SectionReveal>

          <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {content.sections.map((section, index) => {
              const Icon = section.icon;
              return (
                <SectionReveal key={section.title} delay={index * 0.04}>
                  <article className="h-full rounded-lg bg-white p-6">
                    <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#f5f5f7] text-[#0071e3]">
                      <Icon size={18} />
                    </div>
                    <h3 className="mt-5 text-xl font-semibold text-[#1d1d1f]">{t(section.title)}</h3>
                    <p className="mt-3 text-sm leading-7 text-[#6e6e73]">{t(section.description)}</p>
                  </article>
                </SectionReveal>
              );
            })}
          </div>
        </section>

        <section className="bg-white">
          <div className="mx-auto grid max-w-7xl gap-8 px-4 py-16 lg:grid-cols-[minmax(0,1fr)_420px] lg:px-8">
            <SectionReveal>
              <div>
                <h2 className="font-display text-4xl font-semibold tracking-tight text-[#1d1d1f] sm:text-6xl">
                  {t(content.detailTitle)}
                </h2>
                <p className="mt-4 max-w-2xl text-lg leading-8 text-[#6e6e73]">
                  {t(content.detailSubtitle)}
                </p>
                <div className="mt-8 grid gap-3">
                  {content.details.map((key) => (
                    <div key={key} className="flex items-start gap-3 rounded-lg bg-[#f5f5f7] px-4 py-3">
                      <CheckCircle2 size={17} className="mt-1 shrink-0 text-emerald-700" />
                      <p className="text-sm leading-6 text-[#424245]">{t(key)}</p>
                    </div>
                  ))}
                </div>
              </div>
            </SectionReveal>

            <SectionReveal delay={0.08}>
              <aside className="rounded-lg bg-[#1d1d1f] p-6 text-white">
                <p className="text-sm font-semibold uppercase text-white/50">{t(content.fieldTitle)}</p>
                <div className="mt-5 grid gap-3">
                  {content.fields.map((key) => (
                    <div key={key} className="rounded-lg border border-white/10 bg-white/6 px-4 py-3">
                      <p className="text-sm leading-6 text-white/78">{t(key)}</p>
                    </div>
                  ))}
                </div>
              </aside>
            </SectionReveal>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 py-16 lg:px-8">
          <SectionReveal>
            <div className="grid gap-8 rounded-lg bg-white p-6 lg:grid-cols-[minmax(0,0.86fr)_minmax(0,1.14fr)] lg:p-8">
              <div>
                <p className="text-sm font-semibold uppercase text-[#6e6e73]">{t(content.noteTitle)}</p>
                <p className="mt-4 text-base leading-8 text-[#6e6e73]">{t(content.noteBody)}</p>
              </div>
              <div className="border-t border-slate-200 pt-6 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
                <h2 className="font-display text-3xl font-semibold text-[#1d1d1f]">{t(content.finalTitle)}</h2>
                <p className="mt-4 text-base leading-8 text-[#6e6e73]">{t(content.finalSubtitle)}</p>
                <div className="mt-6 flex flex-wrap gap-3">
                  <ActionLink href={content.primaryHref}>{t(content.primaryCta)}</ActionLink>
                  <ActionLink href={content.secondaryHref} variant="secondary">
                    {t(content.secondaryCta)}
                  </ActionLink>
                </div>
              </div>
            </div>
          </SectionReveal>
        </section>

        <div className="mx-auto max-w-7xl px-4 lg:px-8">
          <SiteFooter variant="public" />
        </div>
      </main>
    </div>
  );
}

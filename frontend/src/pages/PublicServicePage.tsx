import {
  ArrowRight,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  GitBranch,
  Globe,
  Search,
  ShieldCheck,
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

// Reduced from 6 kinds to 2 in Phase 1 repositioning. The legacy kinds
// (b2b-leads / seo-geo / sample-data / data-policy) are gone; users
// hitting their old URLs are 301'd server-side (web/app.py).
export type PublicServicePageKind = "open-source" | "contact";

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
  // b2b-leads + seo-geo blocks deleted in Phase 1 repositioning.
  // Old URLs are 301'd server-side via _REDIRECTS_301 in web/app.py.
  "open-source": {
    path: "/open-source",
    metaTitle: "service.openSource.metaTitle",
    metaDescription: "service.openSource.metaDescription",
    eyebrow: "service.openSource.eyebrow",
    title: "service.openSource.title",
    subtitle: "service.openSource.subtitle",
    primaryCta: "service.openSource.repoCta",
    primaryHref: GITHUB_REPO_URL,
    secondaryCta: "landing.heroPrimaryCta",
    secondaryHref: "/services",
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
  // sample-data block deleted in Phase 1 repositioning.
  contact: {
    path: "/contact",
    metaTitle: "service.contact.metaTitle",
    metaDescription: "service.contact.metaDescription",
    eyebrow: "service.contact.eyebrow",
    title: "service.contact.title",
    subtitle: "service.contact.subtitle",
    primaryCta: "landing.emailCta",
    primaryHref: `mailto:${CONTACT_EMAIL}`,
    secondaryCta: "landing.heroPrimaryCta",
    secondaryHref: "/services",
    highlights: ["service.contact.highlight1", "service.contact.highlight2", "service.contact.highlight3"],
    sectionEyebrow: "service.contact.sectionEyebrow",
    sectionTitle: "service.contact.sectionTitle",
    sectionSubtitle: "service.contact.sectionSubtitle",
    sections: [
      // B2B inquiry types (leads / geo / policy) deleted in repositioning.
      // The remaining "seo" inquiry stands in for customization/support inquiries.
      { icon: Search, title: "service.contact.seoTitle", description: "service.contact.seoDesc" },
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
  // data-policy block deleted in Phase 1 repositioning.
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

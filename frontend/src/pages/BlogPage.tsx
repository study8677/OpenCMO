import { ArrowRight, ArrowUpRight, BookOpenText, Orbit, Radar } from "lucide-react";
import { motion } from "framer-motion";
import { Link } from "react-router";
import { SiteFooter } from "../components/layout/SiteFooter";
import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SectionReveal } from "../components/marketing/SectionReveal";
import {
  BLOG_ARTICLES,
  BLOG_DECISION_ARTICLE_SLUGS,
  BLOG_FEATURED_ARTICLE_SLUG,
  BLOG_PRINCIPLES,
  BLOG_READER_PATHS,
  PUBLIC_BLOG_NAV,
  getLandingPath,
  getLocalizedBlogArticlePath,
} from "../content/marketing";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { useI18n } from "../i18n";
import { getSeoLocaleFromLocale } from "../utils/publicRoutes";

export function BlogPage() {
  const { t, locale } = useI18n();
  const seoLocale = getSeoLocaleFromLocale(locale);
  const featuredArticle = BLOG_ARTICLES.find((article) => article.slug === BLOG_FEATURED_ARTICLE_SLUG) ?? BLOG_ARTICLES[0]!;
  const decisionArticles = BLOG_ARTICLES.filter((article) =>
    BLOG_DECISION_ARTICLE_SLUGS.includes(article.slug as (typeof BLOG_DECISION_ARTICLE_SLUGS)[number]),
  );

  usePublicPageMetadata({
    title: t("blog.metaTitle"),
    description: t("blog.metaDescription"),
    basePath: "/blog",
  });

  return (
    <div className="min-h-screen bg-[#f3efe7] text-slate-950">
      <PublicSiteHeader items={PUBLIC_BLOG_NAV} theme="light" />

      <main className="overflow-hidden pb-20">
        <section className="relative">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(201,111,69,0.12),transparent_26%),radial-gradient(circle_at_86%_14%,rgba(134,200,188,0.14),transparent_22%),linear-gradient(180deg,#f7f3ec_0%,#f3efe7_54%,#efe7db_100%)]" />
          <div className="absolute -left-10 top-24 h-56 w-56 rounded-full bg-[#c96f45]/12 blur-3xl animate-float-slow" />
          <div className="absolute bottom-10 right-[8%] h-64 w-64 rounded-full bg-[#86c8bc]/14 blur-3xl animate-float-slower" />

          <div className="relative mx-auto grid max-w-7xl gap-14 px-4 pb-20 pt-12 lg:grid-cols-[minmax(0,0.84fr)_minmax(420px,1.16fr)] lg:px-8 lg:pt-16">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col justify-center pb-4 lg:pb-10"
            >
              <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#9b5d3b]">
                {t("blog.eyebrow")}
              </p>
              <h1 className="font-display mt-6 max-w-4xl text-5xl font-semibold tracking-tight text-[#0b1420] sm:text-[4.4rem] sm:leading-[0.98] lg:text-[5.6rem] lg:leading-[0.94]">
                {t("blog.title")}
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600 sm:text-xl">
                {t("blog.subtitle")}
              </p>
              <p className="mt-5 max-w-xl text-base leading-8 text-slate-500">
                {t("blog.editorNote")}
              </p>

              <div className="mt-9 flex flex-wrap gap-3">
                <Link
                  to={getLocalizedBlogArticlePath(featuredArticle.slug, seoLocale)}
                  className="inline-flex items-center gap-2 rounded-full bg-[#0b1420] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#162131]"
                >
                  {t("blog.featuredLabel")}
                  <ArrowRight size={16} />
                </Link>
                <Link
                  to="/workspace"
                  className="inline-flex items-center gap-2 rounded-full border border-black/8 bg-white/72 px-5 py-3 text-sm font-semibold text-slate-900 transition-colors hover:bg-white"
                >
                  {t("blog.workspaceCta")}
                </Link>
              </div>

              <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-sm font-medium text-slate-500">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">{t("blog.featuredLabel")}</span>
                  <span className="font-semibold text-slate-800">{t(featuredArticle.category)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">{t("blog.libraryTitle")}</span>
                  <span className="font-semibold text-slate-800">{BLOG_ARTICLES.length}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">{t("blog.buyingTrackEyebrow")}</span>
                  <span className="font-semibold text-slate-800">{decisionArticles.length}</span>
                </div>
              </div>
            </motion.div>

            <motion.article
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
              className="relative overflow-hidden rounded-[2.8rem] bg-[#08131d] p-5 text-white shadow-[0_40px_120px_rgba(8,19,29,0.18)] sm:p-7"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${featuredArticle.accentClass}`} />
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(201,111,69,0.16),transparent_24%),linear-gradient(180deg,rgba(8,19,29,0.24),rgba(8,19,29,0.78))]" />

              <div className="relative">
                <div className="flex flex-wrap items-start justify-between gap-4 border-b border-white/10 pb-5">
                  <div className="max-w-sm">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#f3dcc9]">
                      {t("blog.featuredLabel")}
                    </p>
                    <div className="mt-3 flex items-center gap-2 text-sm text-white/68">
                      <BookOpenText size={15} />
                      <span>{t(featuredArticle.category)}</span>
                    </div>
                  </div>
                  <div className="rounded-full border border-white/12 bg-white/6 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-white/70">
                    {featuredArticle.index}
                  </div>
                </div>

                <h2 className="font-display mt-6 max-w-2xl text-3xl font-semibold tracking-tight sm:text-[2.4rem] sm:leading-[1.02]">
                  {t(featuredArticle.title)}
                </h2>
                <p className="mt-4 max-w-2xl text-base leading-8 text-white/70">
                  {t(featuredArticle.summary)}
                </p>

                <div className="mt-6 space-y-3">
                  {featuredArticle.takeawayKeys.map((key, index) => (
                    <div
                      key={key}
                      className="grid gap-3 rounded-[1.5rem] border border-white/10 bg-white/5 px-4 py-4 sm:grid-cols-[48px_minmax(0,1fr)]"
                    >
                      <span className="font-display text-2xl font-semibold tracking-tight text-white/26">
                        {`${index + 1}`.padStart(2, "0")}
                      </span>
                      <p className="text-sm leading-7 text-white/80">{t(key)}</p>
                    </div>
                  ))}
                </div>

                <div className="mt-6 grid gap-4 border-t border-white/10 pt-6 sm:grid-cols-2">
                  <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/40">
                      {t("blog.audienceLabel")}
                    </p>
                    <p className="mt-3 text-sm leading-7 text-white/72">{t(featuredArticle.audience)}</p>
                  </div>
                  <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white/40">
                      {t("blog.thesisLabel")}
                    </p>
                    <p className="mt-3 text-sm leading-7 text-white/72">{t(featuredArticle.thesis)}</p>
                  </div>
                </div>

                <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-white/10 pt-6">
                  <span className="text-sm font-medium text-white/60">{t(featuredArticle.readTime)}</span>
                  <Link
                    to={getLocalizedBlogArticlePath(featuredArticle.slug, seoLocale)}
                    className="inline-flex items-center gap-2 text-sm font-semibold text-white transition-colors hover:text-[#f3dcc9]"
                  >
                    {t("blog.readArticleCta")}
                    <ArrowUpRight size={15} />
                  </Link>
                </div>
              </div>
            </motion.article>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 pt-20 lg:px-8 lg:pt-24">
          <SectionReveal>
            <div className="grid gap-8 lg:grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] lg:items-end">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#9b5d3b]">
                  {t("blog.buyingTrackEyebrow")}
                </p>
                <h2 className="font-display mt-4 max-w-xl text-4xl font-semibold tracking-tight text-[#0b1420] sm:text-[3.4rem] sm:leading-[1.02]">
                  {t("blog.buyingTrackTitle")}
                </h2>
              </div>
              <p className="max-w-2xl text-lg leading-8 text-slate-600">
                {t("blog.buyingTrackSubtitle")}
              </p>
            </div>
          </SectionReveal>

          <div className="mt-16 grid gap-6 lg:grid-cols-2">
            {decisionArticles.map((article, index) => (
              <SectionReveal key={article.slug} delay={index * 0.06}>
                <Link
                  to={getLocalizedBlogArticlePath(article.slug, seoLocale)}
                  className={`group block overflow-hidden rounded-[2.4rem] border border-black/8 bg-gradient-to-br p-6 shadow-[0_24px_80px_rgba(8,19,29,0.07)] transition-transform duration-300 hover:-translate-y-1 sm:p-7 ${article.accentClass}`}
                >
                  <div className="rounded-[2rem] bg-white/78 p-5 sm:p-6">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
                        {t(article.category)}
                      </p>
                      <span className="rounded-full border border-black/8 bg-white/80 px-3 py-1 text-xs font-semibold text-slate-600">
                        {article.index}
                      </span>
                    </div>
                    <h3 className="font-display mt-5 text-3xl font-semibold tracking-tight text-[#0b1420] sm:text-[2.2rem] sm:leading-[1.04]">
                      {t(article.title)}
                    </h3>
                    <p className="mt-4 text-base leading-8 text-slate-600">
                      {t(article.summary)}
                    </p>
                    <div className="mt-5 rounded-[1.5rem] border border-black/8 bg-[#f8f4ed] p-4 text-sm leading-7 text-slate-700">
                      {t(article.highlight)}
                    </div>
                    <div className="mt-6 flex items-center justify-between border-t border-black/8 pt-5 text-sm font-semibold text-slate-700">
                      <span>{t(article.readTime)}</span>
                      <span className="inline-flex items-center gap-2 text-slate-900 transition-transform group-hover:translate-x-0.5">
                        {t("blog.readArticleCta")}
                        <ArrowRight size={15} />
                      </span>
                    </div>
                  </div>
                </Link>
              </SectionReveal>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 pt-20 lg:px-8 lg:pt-24">
          <SectionReveal>
            <div className="overflow-hidden rounded-[2.8rem] border border-black/8 bg-white/72 shadow-[0_24px_80px_rgba(8,19,29,0.07)]">
              <div className="grid gap-10 px-6 py-8 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.94fr)] lg:px-8 lg:py-10">
                <div>
                  <div className="flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#0b1420] text-white">
                      <Orbit size={18} />
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#9b5d3b]">
                        {t("blog.principlesEyebrow")}
                      </p>
                      <h2 className="font-display mt-2 text-3xl font-semibold tracking-tight text-[#0b1420]">
                        {t("blog.principlesTitle")}
                      </h2>
                    </div>
                  </div>

                  <div className="mt-8">
                    {BLOG_PRINCIPLES.map((item, index) => (
                      <div
                        key={item.title}
                        className="grid gap-4 border-t border-black/8 py-5 sm:grid-cols-[56px_minmax(0,1fr)]"
                      >
                        <div className="font-display text-3xl font-semibold tracking-tight text-[#c96f45]">
                          {`${index + 1}`.padStart(2, "0")}
                        </div>
                        <div>
                          <h3 className="font-display text-2xl font-semibold tracking-tight text-[#0b1420]">
                            {t(item.title)}
                          </h3>
                          <p className="mt-3 text-base leading-8 text-slate-600">
                            {t(item.description)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[2.2rem] bg-[#f0e7db] p-6 sm:p-7">
                  <div className="flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-[#0b1420] shadow-[0_10px_24px_rgba(8,19,29,0.08)]">
                      <Radar size={18} />
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#9b5d3b]">
                        {t("blog.readingPathsEyebrow")}
                      </p>
                      <h2 className="font-display mt-2 text-3xl font-semibold tracking-tight text-[#0b1420]">
                        {t("blog.readingPathsTitle")}
                      </h2>
                    </div>
                  </div>

                  <div className="mt-8 space-y-3">
                    {BLOG_READER_PATHS.map((item) => (
                      <div key={item.title} className="rounded-[1.6rem] border border-black/8 bg-white/74 p-4">
                        <h3 className="font-display text-xl font-semibold tracking-tight text-[#0b1420]">
                          {t(item.title)}
                        </h3>
                        <p className="mt-2 text-sm leading-7 text-slate-600">
                          {t(item.description)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </SectionReveal>
        </section>

        <section className="mx-auto max-w-7xl px-4 pt-20 lg:px-8 lg:pt-24">
          <SectionReveal>
            <div className="flex flex-col gap-4 border-b border-black/8 pb-8 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-3xl">
                <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-[#9b5d3b]">
                  {t("blog.libraryTitle")}
                </p>
                <h2 className="font-display mt-4 text-4xl font-semibold tracking-tight text-[#0b1420] sm:text-[3.4rem] sm:leading-[1.02]">
                  {t("blog.librarySubtitle")}
                </h2>
              </div>
              <Link
                to={getLandingPath(seoLocale)}
                className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 transition-colors hover:text-slate-950"
              >
                {t("blog.homeCta")}
                <ArrowUpRight size={15} />
              </Link>
            </div>
          </SectionReveal>

          <div className="mt-12 overflow-hidden rounded-[2.8rem] border border-black/8 bg-white/72 shadow-[0_24px_80px_rgba(8,19,29,0.07)]">
            {BLOG_ARTICLES.map((article, index) => (
              <SectionReveal
                key={article.slug}
                delay={index * 0.03}
                className="border-t border-black/8 first:border-t-0"
              >
                <Link
                  to={getLocalizedBlogArticlePath(article.slug, seoLocale)}
                  className="group grid gap-5 px-6 py-6 transition-colors hover:bg-white/65 sm:px-7 lg:grid-cols-[92px_minmax(0,0.88fr)_minmax(0,1.12fr)_auto] lg:items-center"
                >
                  <div className="flex items-center justify-between gap-4 lg:block">
                    <div className="font-display text-4xl font-semibold tracking-tight text-slate-300">
                      {article.index}
                    </div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                      {t(article.category)}
                    </p>
                  </div>

                  <div>
                    <h3 className="font-display text-2xl font-semibold tracking-tight text-[#0b1420]">
                      {t(article.title)}
                    </h3>
                    <p className="mt-3 text-sm font-medium text-slate-500">{t(article.readTime)}</p>
                  </div>

                  <div className="max-w-2xl">
                    <p className="text-base leading-8 text-slate-600">{t(article.summary)}</p>
                  </div>

                  <div className="inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition-transform group-hover:translate-x-0.5">
                    {t("blog.readArticleCta")}
                    <ArrowUpRight size={15} />
                  </div>
                </Link>
              </SectionReveal>
            ))}
          </div>
        </section>

        <div className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SiteFooter variant="public" />
        </div>
      </main>
    </div>
  );
}

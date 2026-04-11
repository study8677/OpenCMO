import { ArrowRight, ArrowUpRight, BookOpenText, NotebookPen, Orbit, Radar, ScrollText } from "lucide-react";
import { motion } from "framer-motion";
import { Link } from "react-router";
import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SectionReveal } from "../components/marketing/SectionReveal";
import { SiteFooter } from "../components/layout/SiteFooter";
import {
  BLOG_ARTICLES,
  BLOG_DECISION_ARTICLE_SLUGS,
  BLOG_PRINCIPLES,
  BLOG_READER_PATHS,
  PUBLIC_BLOG_NAV,
} from "../content/marketing";
import { usePageMetadata } from "../hooks/usePageMetadata";
import { useI18n } from "../i18n";

export function BlogPage() {
  const { t } = useI18n();
  const featuredArticle =
    BLOG_ARTICLES.find((article) => article.slug === BLOG_DECISION_ARTICLE_SLUGS[0]) ?? BLOG_ARTICLES[0]!;
  const decisionArticles = BLOG_ARTICLES.filter((article) =>
    BLOG_DECISION_ARTICLE_SLUGS.includes(article.slug as (typeof BLOG_DECISION_ARTICLE_SLUGS)[number])
  );
  const articleDirectoryColumns = [BLOG_ARTICLES.slice(0, 3), BLOG_ARTICLES.slice(3)];

  usePageMetadata({
    title: t("blog.metaTitle"),
    description: t("blog.metaDescription"),
    canonicalPath: "/blog",
  });

  return (
    <div className="min-h-screen bg-[#f6efe5] text-slate-950">
      <PublicSiteHeader items={PUBLIC_BLOG_NAV} theme="light" />

      <main className="pb-16">
        <section className="relative overflow-hidden border-b border-black/8 bg-[#08141f] text-white">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(201,111,69,0.28),transparent_30%),radial-gradient(circle_at_82%_18%,rgba(134,200,188,0.22),transparent_26%),linear-gradient(135deg,#08141f_0%,#0c2538_48%,#08141f_100%)]" />
          <div className="absolute left-[-6%] top-20 h-48 w-48 rounded-full bg-[#c96f45]/20 blur-3xl animate-float-slow" />
          <div className="absolute bottom-10 right-[8%] h-56 w-56 rounded-full bg-[#86c8bc]/16 blur-3xl animate-float-slower" />

          <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-16 lg:grid-cols-[minmax(0,0.95fr)_minmax(360px,0.85fr)] lg:px-8 lg:py-24">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
            >
              <p className="inline-flex rounded-full border border-white/14 bg-white/7 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-[#f3dcc9]">
                {t("blog.eyebrow")}
              </p>
              <h1 className="font-display mt-6 max-w-4xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-[3.2rem] lg:leading-[1.04] xl:text-[3.9rem] xl:leading-[1.01]">
                {t("blog.title")}
              </h1>
              <p className="mt-5 max-w-3xl text-lg leading-8 text-white/72 sm:text-xl">
                {t("blog.subtitle")}
              </p>
              <p className="mt-4 max-w-3xl text-base leading-7 text-[#f3dcc9]">
                {t("blog.editorNote")}
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href={`#${featuredArticle.slug}`}
                  className="inline-flex items-center gap-2 rounded-full bg-[#f7ecde] px-5 py-3 text-sm font-semibold text-[#082032] transition-colors hover:bg-white"
                >
                  {t("blog.featuredLabel")}
                  <ArrowRight size={16} />
                </a>
                <Link
                  to="/workspace"
                  className="inline-flex items-center gap-2 rounded-full border border-white/16 bg-white/7 px-5 py-3 text-sm font-semibold text-white transition-colors hover:border-white/30 hover:bg-white/10"
                >
                  {t("blog.workspaceCta")}
                </Link>
              </div>
            </motion.div>

            <motion.article
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.85, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
              className="relative overflow-hidden rounded-[2rem] border border-white/12 bg-[linear-gradient(145deg,rgba(255,255,255,0.08),rgba(255,255,255,0.03))] p-6 shadow-[0_28px_100px_rgba(0,0,0,0.28)]"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${featuredArticle.accentClass}`} />
              <div className="absolute right-5 top-5 rounded-full border border-white/14 bg-[#08141f]/70 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-white/70">
                {featuredArticle.index}
              </div>
              <div className="relative">
                <div className="flex items-center gap-2 text-sm text-white/70">
                  <BookOpenText size={15} />
                  <span>{t(featuredArticle.category)}</span>
                </div>
                <h2 className="font-display mt-6 max-w-xl text-3xl font-semibold tracking-tight text-white">
                  {t(featuredArticle.title)}
                </h2>
                <p className="mt-4 max-w-xl text-base leading-7 text-white/74">
                  {t(featuredArticle.summary)}
                </p>
                <div className="mt-8 grid gap-3 sm:grid-cols-2">
                  {featuredArticle.takeawayKeys.map((key) => (
                    <div key={key} className="rounded-2xl border border-white/10 bg-[#08141f]/62 p-4 text-sm leading-6 text-white/76">
                      {t(key)}
                    </div>
                  ))}
                </div>
                <div className="mt-5 grid gap-3 border-t border-white/10 pt-5 text-sm text-white/74">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/42">
                      {t("blog.audienceLabel")}
                    </p>
                    <p className="mt-2 leading-6">{t(featuredArticle.audience)}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/42">
                      {t("blog.thesisLabel")}
                    </p>
                    <p className="mt-2 leading-6">{t(featuredArticle.thesis)}</p>
                  </div>
                </div>
              </div>
            </motion.article>
          </div>
        </section>

        <SectionReveal className="mx-auto max-w-7xl px-4 pt-14 lg:px-8">
          <div className="rounded-[2rem] border border-black/8 bg-white/74 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.06)] sm:p-8">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#c96f45]">
                {t("blog.buyingTrackEyebrow")}
              </p>
              <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                {t("blog.buyingTrackTitle")}
              </h2>
              <p className="mt-4 text-base leading-8 text-slate-700">
                {t("blog.buyingTrackSubtitle")}
              </p>
            </div>

            <div className="mt-8 grid gap-5 lg:grid-cols-2">
              {decisionArticles.map((article) => (
                <a
                  key={article.slug}
                  href={`#${article.slug}`}
                  className={`group relative overflow-hidden rounded-[1.8rem] border border-black/8 bg-gradient-to-br p-6 shadow-[0_18px_50px_rgba(8,32,50,0.08)] transition-transform duration-300 hover:-translate-y-1 ${article.accentClass}`}
                >
                  <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.42),rgba(255,255,255,0.82))]" />
                  <div className="relative flex h-full flex-col">
                    <div className="flex items-start justify-between gap-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                        {t(article.category)}
                      </p>
                      <span className="rounded-full border border-black/8 bg-white/78 px-2.5 py-1 text-xs font-semibold text-slate-600">
                        {article.index}
                      </span>
                    </div>
                    <h3 className="font-display mt-5 text-2xl font-semibold tracking-tight text-slate-950">
                      {t(article.title)}
                    </h3>
                    <p className="mt-3 text-sm leading-7 text-slate-700">
                      {t(article.summary)}
                    </p>
                    <div className="mt-5 rounded-2xl border border-black/8 bg-white/72 p-4 text-sm leading-6 text-slate-700">
                      {t(article.highlight)}
                    </div>
                    <div className="mt-5 space-y-2 border-t border-black/8 pt-4">
                      {article.takeawayKeys.map((key) => (
                        <p key={key} className="text-sm leading-6 text-slate-700">
                          {t(key)}
                        </p>
                      ))}
                    </div>
                    <div className="mt-6 flex items-center justify-between text-sm font-semibold text-slate-700">
                      <span>{t(article.readTime)}</span>
                      <span className="inline-flex items-center gap-1 text-slate-900">
                        {t("blog.readArticleCta")}
                        <ArrowRight size={15} className="transition-transform group-hover:translate-x-1" />
                      </span>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </SectionReveal>

        <SectionReveal className="mx-auto max-w-7xl px-4 pt-14 lg:px-8">
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1.05fr)_minmax(340px,0.95fr)]">
            <div className="rounded-[2rem] border border-black/8 bg-white/70 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.05)]">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#082032] text-white">
                  <Orbit size={18} />
                </div>
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#c96f45]">
                    {t("blog.principlesEyebrow")}
                  </p>
                  <h2 className="font-display mt-1 text-3xl font-semibold tracking-tight text-slate-950">
                    {t("blog.principlesTitle")}
                  </h2>
                </div>
              </div>
              <div className="mt-8 grid gap-4">
                {BLOG_PRINCIPLES.map((item, index) => (
                  <div key={item.title} className="grid gap-3 rounded-[1.4rem] border border-black/8 bg-[#f8f4ed] p-4 sm:grid-cols-[56px_minmax(0,1fr)]">
                    <div className="font-display text-3xl font-semibold tracking-tight text-[#c96f45]">
                      0{index + 1}
                    </div>
                    <div>
                      <h3 className="font-display text-xl font-semibold tracking-tight text-slate-950">
                        {t(item.title)}
                      </h3>
                      <p className="mt-2 text-sm leading-7 text-slate-700">
                        {t(item.description)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[2rem] border border-black/8 bg-[#efe5d6] p-6 shadow-[0_18px_60px_rgba(8,32,50,0.06)]">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-[#082032] shadow-sm">
                  <Radar size={18} />
                </div>
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#c96f45]">
                    {t("blog.readingPathsEyebrow")}
                  </p>
                  <h2 className="font-display mt-1 text-3xl font-semibold tracking-tight text-slate-950">
                    {t("blog.readingPathsTitle")}
                  </h2>
                </div>
              </div>
              <div className="mt-8 space-y-4">
                {BLOG_READER_PATHS.map((item) => (
                  <div key={item.title} className="rounded-[1.4rem] border border-black/8 bg-white/78 p-4">
                    <h3 className="font-display text-xl font-semibold tracking-tight text-slate-950">
                      {t(item.title)}
                    </h3>
                    <p className="mt-2 text-sm leading-7 text-slate-700">
                      {t(item.description)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </SectionReveal>

        <SectionReveal className="mx-auto max-w-7xl px-4 pt-14 lg:px-8">
          <div className="flex flex-col gap-4 border-b border-black/8 pb-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#c96f45]">
                {t("blog.libraryTitle")}
              </p>
              <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                {t("blog.librarySubtitle")}
              </h2>
            </div>
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 transition-colors hover:text-slate-950"
            >
              {t("blog.homeCta")}
              <ArrowUpRight size={15} />
            </Link>
          </div>

          <div className="mt-10 grid gap-6 lg:grid-cols-[minmax(260px,0.72fr)_minmax(0,1.28fr)]">
            <div className="rounded-[2rem] border border-black/8 bg-white/78 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.05)]">
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[#c96f45]">
                {t("blog.featuredLabel")}
              </p>
              <h3 className="font-display mt-4 text-2xl font-semibold tracking-tight text-slate-950">
                {t(featuredArticle.title)}
              </h3>
              <p className="mt-3 text-sm leading-7 text-slate-700">
                {t(featuredArticle.summary)}
              </p>
              <div className="mt-5 rounded-[1.4rem] border border-black/8 bg-[#f8f4ed] p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                  {t("blog.thesisLabel")}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-700">
                  {t(featuredArticle.thesis)}
                </p>
              </div>
              <a
                href={`#${featuredArticle.slug}`}
                className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-slate-900 transition-colors hover:text-[#082032]"
              >
                {t("blog.readArticleCta")}
                <ArrowRight size={15} />
              </a>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {articleDirectoryColumns.map((column, columnIndex) => (
                <div key={columnIndex} className="grid gap-4">
                  {column.map((article) => (
                    <a
                      key={article.slug}
                      href={`#${article.slug}`}
                      className="group rounded-[1.6rem] border border-black/8 bg-white/78 p-5 shadow-[0_18px_50px_rgba(8,32,50,0.05)] transition-transform duration-300 hover:-translate-y-1"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                          {t(article.category)}
                        </p>
                        <span className="rounded-full border border-black/8 bg-[#f8f4ed] px-2.5 py-1 text-xs font-semibold text-slate-600">
                          {article.index}
                        </span>
                      </div>
                      <h3 className="font-display mt-4 text-xl font-semibold tracking-tight text-slate-950">
                        {t(article.title)}
                      </h3>
                      <p className="mt-3 text-sm leading-7 text-slate-700">
                        {t(article.summary)}
                      </p>
                      <div className="mt-4 flex items-center justify-between border-t border-black/8 pt-4 text-sm font-semibold text-slate-700">
                        <span>{t(article.readTime)}</span>
                        <span className="inline-flex items-center gap-1 text-slate-900">
                          {t("blog.readArticleCta")}
                          <ArrowUpRight size={15} className="transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                        </span>
                      </div>
                    </a>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </SectionReveal>

        <SectionReveal className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#c96f45]">
              {t("blog.deepDiveTitle")}
            </p>
            <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
              {t("blog.deepDiveSubtitle")}
            </h2>
          </div>

          <div className="mt-10 space-y-8">
            {BLOG_ARTICLES.map((article) => (
              <article
                key={article.slug}
                id={article.slug}
                className="rounded-[2rem] border border-black/8 bg-white/80 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.06)] backdrop-blur sm:p-8"
              >
                <div className="grid gap-10 lg:grid-cols-[280px_minmax(0,1fr)]">
                  <div className="lg:sticky lg:top-28 lg:self-start">
                    <div className={`rounded-[1.5rem] bg-gradient-to-br ${article.accentClass} p-5`}>
                      <p className="text-xs font-semibold uppercase tracking-[0.26em] text-slate-500">
                        {t(article.category)}
                      </p>
                      <h3 className="font-display mt-4 text-2xl font-semibold tracking-tight text-slate-950">
                        {t(article.title)}
                      </h3>
                      <p className="mt-3 text-sm leading-7 text-slate-700">
                        {t(article.summary)}
                      </p>
                      <div className="mt-5 rounded-2xl bg-white/72 p-4 text-sm leading-6 text-slate-700">
                        {t(article.highlight)}
                      </div>
                    </div>
                    <div className="mt-4 grid gap-4 rounded-[1.4rem] border border-black/8 bg-[#f8f4ed] p-4 text-sm text-slate-700">
                      <div className="flex items-center gap-2 font-semibold text-slate-600">
                        <NotebookPen size={15} />
                        <span>{t(article.readTime)}</span>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                          {t("blog.audienceLabel")}
                        </p>
                        <p className="mt-2 leading-6">{t(article.audience)}</p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                          {t("blog.thesisLabel")}
                        </p>
                        <p className="mt-2 leading-6">{t(article.thesis)}</p>
                      </div>
                    </div>
                    <div className="mt-4 rounded-[1.4rem] border border-black/8 bg-white/72 p-4">
                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                        <ScrollText size={15} />
                        <span>{t("blog.takeawaysLabel")}</span>
                      </div>
                      <div className="mt-3 space-y-3">
                        {article.takeawayKeys.map((key) => (
                          <p key={key} className="text-sm leading-6 text-slate-700">
                            {t(key)}
                          </p>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    {article.sections.map((section) => (
                      <section key={section.title} className="border-b border-black/6 pb-6 last:border-none last:pb-0">
                        <h4 className="font-display text-2xl font-semibold tracking-tight text-slate-950">
                          {t(section.title)}
                        </h4>
                        <p className="mt-4 max-w-3xl text-base leading-8 text-slate-700">
                          {t(section.body)}
                        </p>
                      </section>
                    ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </SectionReveal>

        <div className="mx-auto max-w-7xl px-4 pt-16 lg:px-8">
          <SiteFooter />
        </div>
      </main>
    </div>
  );
}

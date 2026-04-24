import { ArrowLeft, ArrowUpRight, NotebookPen, ScrollText } from "lucide-react";
import { Link, Navigate, useParams } from "react-router";
import { SiteFooter } from "../components/layout/SiteFooter";
import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SectionReveal } from "../components/marketing/SectionReveal";
import {
  BLOG_ARTICLES,
  PUBLIC_BLOG_NAV,
  findBlogArticleBySlug,
  getBlogIndexPath,
  getLocalizedBlogArticlePath,
} from "../content/marketing";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { useI18n } from "../i18n";
import { getSeoLocaleFromLocale } from "../utils/publicRoutes";

export function BlogArticlePage() {
  const { slug = "" } = useParams();
  const { t, locale } = useI18n();
  const seoLocale = getSeoLocaleFromLocale(locale);
  const article = findBlogArticleBySlug(slug);

  if (!article) {
    return <Navigate to={getBlogIndexPath(seoLocale)} replace />;
  }

  const relatedArticles = BLOG_ARTICLES.filter((item) => item.slug !== article.slug).slice(0, 3);

  usePublicPageMetadata({
    title: `${t(article.title)} | OpenCMO Blog`,
    description: t(article.summary),
    basePath: `/blog/${article.slug}`,
  });

  return (
    <div className="min-h-screen bg-[#f6efe5] text-slate-950">
      <PublicSiteHeader items={PUBLIC_BLOG_NAV} theme="light" />

      <main className="pb-16">
        <section className="relative overflow-hidden border-b border-black/8 bg-[#08141f] text-white">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_16%,rgba(201,111,69,0.28),transparent_24%),radial-gradient(circle_at_82%_18%,rgba(134,200,188,0.2),transparent_24%),linear-gradient(135deg,#08141f_0%,#0c2538_46%,#08141f_100%)]" />

          <div className="relative mx-auto max-w-5xl px-4 py-16 lg:px-8 lg:py-20">
            <Link
              to={getBlogIndexPath(seoLocale)}
              className="inline-flex items-center gap-2 rounded-full border border-white/14 bg-white/8 px-4 py-2 text-sm font-semibold text-white transition-colors hover:border-white/28 hover:bg-white/12"
            >
              <ArrowLeft size={15} />
              {t("landing.navBlog")}
            </Link>

            <article className="mt-8">
              <div className="flex flex-wrap items-center gap-3 text-sm text-[#f3dcc9]">
                <span className="rounded-full border border-white/14 bg-white/8 px-3 py-1 font-semibold uppercase tracking-[0.22em]">
                  {t(article.category)}
                </span>
                <span className="inline-flex items-center gap-2">
                  <NotebookPen size={15} />
                  {t(article.readTime)}
                </span>
              </div>

              <h1 className="font-display mt-6 max-w-4xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-[3.4rem] lg:leading-[1.02]">
                {t(article.title)}
              </h1>
              <p className="mt-5 max-w-3xl text-lg leading-8 text-white/72 sm:text-xl">
                {t(article.summary)}
              </p>
              <div className="mt-6 rounded-[1.6rem] border border-white/12 bg-white/7 p-5 text-base leading-8 text-white/76">
                {t(article.highlight)}
              </div>
            </article>
          </div>
        </section>

        <SectionReveal className="mx-auto max-w-5xl px-4 pt-12 lg:px-8">
          <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
            <aside className="space-y-4 lg:sticky lg:top-28 lg:self-start">
              <div className={`rounded-[1.6rem] border border-black/8 bg-gradient-to-br ${article.accentClass} p-5 shadow-[0_18px_50px_rgba(8,32,50,0.08)]`}>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                  {t("blog.audienceLabel")}
                </p>
                <p className="mt-3 text-sm leading-7 text-slate-800">
                  {t(article.audience)}
                </p>
                <div className="mt-5 border-t border-black/8 pt-5">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                    {t("blog.thesisLabel")}
                  </p>
                  <p className="mt-3 text-sm leading-7 text-slate-800">
                    {t(article.thesis)}
                  </p>
                </div>
              </div>

              <div className="rounded-[1.6rem] border border-black/8 bg-white/78 p-5 shadow-[0_18px_50px_rgba(8,32,50,0.05)]">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <ScrollText size={15} />
                  <span>{t("blog.takeawaysLabel")}</span>
                </div>
                <div className="mt-4 space-y-3">
                  {article.takeawayKeys.map((key) => (
                    <p key={key} className="text-sm leading-6 text-slate-700">
                      {t(key)}
                    </p>
                  ))}
                </div>
              </div>
            </aside>

            <article className="rounded-[2rem] border border-black/8 bg-white/80 p-6 shadow-[0_18px_60px_rgba(8,32,50,0.06)] sm:p-8">
              <div className="space-y-8">
                {article.sections.map((section) => (
                  <section key={section.title} className="border-b border-black/6 pb-8 last:border-none last:pb-0">
                    <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-950 sm:text-[2rem]">
                      {t(section.title)}
                    </h2>
                    <p className="mt-4 max-w-3xl text-base leading-8 text-slate-700">
                      {t(section.body)}
                    </p>
                  </section>
                ))}
              </div>
            </article>
          </div>
        </SectionReveal>

        <SectionReveal className="mx-auto max-w-5xl px-4 pt-14 lg:px-8">
          <div className="flex flex-col gap-4 border-b border-black/8 pb-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#c96f45]">
                {t("blog.libraryTitle")}
              </p>
              <h2 className="font-display mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                {t("blog.deepDiveSubtitle")}
              </h2>
            </div>
            <Link
              to={getBlogIndexPath(seoLocale)}
              className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 transition-colors hover:text-slate-950"
            >
              {t("landing.navBlog")}
              <ArrowUpRight size={15} />
            </Link>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {relatedArticles.map((item) => (
              <Link
                key={item.slug}
                to={getLocalizedBlogArticlePath(item.slug, seoLocale)}
                className="group rounded-[1.6rem] border border-black/8 bg-white/78 p-5 shadow-[0_18px_50px_rgba(8,32,50,0.05)] transition-transform duration-300 hover:-translate-y-1"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                  {t(item.category)}
                </p>
                <h3 className="font-display mt-4 text-xl font-semibold tracking-tight text-slate-950">
                  {t(item.title)}
                </h3>
                <p className="mt-3 text-sm leading-7 text-slate-700">
                  {t(item.summary)}
                </p>
                <div className="mt-4 flex items-center justify-between border-t border-black/8 pt-4 text-sm font-semibold text-slate-700">
                  <span>{t(item.readTime)}</span>
                  <span className="inline-flex items-center gap-1 text-slate-900">
                    {t("blog.readArticleCta")}
                    <ArrowUpRight size={15} className="transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </SectionReveal>

        <div className="mx-auto max-w-5xl px-4 pt-16 lg:px-8">
          <SiteFooter variant="public" />
        </div>
      </main>
    </div>
  );
}

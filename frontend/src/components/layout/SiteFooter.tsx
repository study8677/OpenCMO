import { ExternalLink, Github, Link2 } from "lucide-react";
import { useSiteStats } from "../../hooks/useSiteStats";
import { useI18n } from "../../i18n";

const GITHUB_REPO = "https://github.com/study8677/OpenCMO";
const FRIEND_LINKS = [
  {
    href: "https://okara.ai/",
    labelKey: "siteFooter.okara",
  },
] as const;

export function SiteFooter() {
  const { t, locale } = useI18n();
  const { data: siteStats } = useSiteStats();
  const numberFormatter = new Intl.NumberFormat(locale);

  return (
    <footer className="mt-10 border-t border-slate-200/80 pt-6 pb-8 text-sm text-slate-500">
      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <div className="space-y-2">
          <p className="text-sm font-semibold text-slate-900">OpenCMO</p>
          <p className="max-w-sm leading-6 text-slate-500">
            {t("siteFooter.description")}
          </p>
        </div>

        <div className="space-y-2">
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
            <Github size={14} />
            {t("siteFooter.sourceCode")}
          </p>
          <a
            href={GITHUB_REPO}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800"
          >
            {t("siteFooter.githubRepo")}
            <ExternalLink size={14} />
          </a>
        </div>

        <div className="space-y-2">
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
            <Link2 size={14} />
            {t("siteFooter.friendLinks")}
          </p>
          <div className="flex flex-wrap gap-2">
            {FRIEND_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-slate-300 hover:text-slate-900"
              >
                {t(link.labelKey)}
                <ExternalLink size={14} />
              </a>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
            {t("siteFooter.liveStats")}
          </p>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                {t("siteFooter.totalVisits")}
              </p>
              <p className="mt-2 text-lg font-semibold text-slate-900">
                {numberFormatter.format(siteStats?.total_visits ?? 0)}
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                {t("siteFooter.uniqueVisitors")}
              </p>
              <p className="mt-2 text-lg font-semibold text-slate-900">
                {numberFormatter.format(siteStats?.unique_visitors ?? 0)}
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

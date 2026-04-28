import { ExternalLink, LayoutDashboard, Sparkles } from "lucide-react";
import type { MouseEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { useI18n } from "../../i18n";
import { LOCALE_LABELS, SUPPORTED_LOCALES, type Locale } from "../../i18n/locale";
import type { PublicNavItem } from "../../content/marketing";
import {
  getLocalizedCurrentPublicPath,
  getLocalizedPublicPath,
  getSeoLocaleFromLocale,
  isPublicRoutePath,
} from "../../utils/publicRoutes";

const GITHUB_REPO = "https://github.com/study8677/OpenCMO";
const CONTACT_EMAIL = "hello@aidcmo.com";

type PublicSiteHeaderProps = {
  items: PublicNavItem[];
  theme?: "dark" | "light";
};

function PublicNavLink({
  href,
  label,
  className,
}: { href: string; label: string; className: string }) {
  if (href.startsWith("#")) {
    const scrollToSection = (event: MouseEvent<HTMLAnchorElement>) => {
      const target = document.getElementById(href.slice(1));
      if (!target) return;

      event.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      window.history.replaceState(null, "", href);
    };

    return (
      <a href={href} className={className} onClick={scrollToSection}>
        {label}
      </a>
    );
  }

  return (
    <Link to={href} className={className}>
      {label}
    </Link>
  );
}

export function PublicSiteHeader({
  items,
  theme = "dark",
}: PublicSiteHeaderProps) {
  const { t, locale, setLocale } = useI18n();
  const location = useLocation();
  const navigate = useNavigate();
  const isPublicRoute = isPublicRoutePath(location.pathname);
  const seoLocale = getSeoLocaleFromLocale(locale);

  const nextLocale = () => {
    if (isPublicRoute) {
      const nextSeoLocale = seoLocale === "en" ? "zh" : "en";
      const localizedPath = getLocalizedCurrentPublicPath(location.pathname, nextSeoLocale);
      setLocale(nextSeoLocale);
      if (localizedPath) {
        navigate(`${localizedPath}${location.search}${location.hash}`);
      }
      return;
    }

    const idx = SUPPORTED_LOCALES.indexOf(locale);
    const next = SUPPORTED_LOCALES[((idx === -1 ? 0 : idx) + 1) % SUPPORTED_LOCALES.length] as Locale;
    setLocale(next);
  };

  const publicHref = (href: string) => {
    if (href.startsWith("#") || !isPublicRoute) {
      return href;
    }
    if (!isPublicRoutePath(href)) {
      return href;
    }
    return getLocalizedPublicPath(href, seoLocale);
  };

  const homeHref = isPublicRoute ? getLocalizedPublicPath("/", seoLocale) : "/";

  const wrapperClass =
    theme === "dark"
      ? "border-white/10 bg-[#08141f]/72 text-white backdrop-blur-xl"
      : "border-slate-950/6 bg-white/72 text-slate-950 backdrop-blur-xl";
  const brandIconClass =
    theme === "dark"
      ? "bg-[#c96f45] text-white shadow-[0_14px_30px_rgba(201,111,69,0.28)]"
      : "border border-slate-200 bg-white text-slate-900 shadow-[0_10px_24px_rgba(15,23,42,0.06)]";
  const brandMetaClass =
    theme === "dark" ? "text-white/60" : "text-slate-500";
  const navClass =
    theme === "dark"
      ? "text-sm font-medium text-white/70 transition-colors hover:text-white"
      : "text-sm font-medium text-slate-600 transition-colors hover:text-slate-950";
  const localeClass =
    theme === "dark"
      ? "border-white/15 bg-white/6 text-white/80 hover:border-white/25 hover:text-white"
      : "border-slate-200 bg-white/80 text-slate-700 hover:border-slate-300 hover:text-slate-950";
  const githubClass =
    theme === "dark"
      ? "border-white/15 bg-white/6 text-white/80 hover:border-white/25 hover:text-white"
      : "border-slate-200 bg-white/80 text-slate-700 hover:border-slate-300 hover:text-slate-950";
  const workspaceClass =
    theme === "dark"
      ? "bg-[#f7ecde] text-[#082032] hover:bg-white"
      : "bg-[#082032] text-white hover:bg-[#0c2538]";

  return (
    <header className={`sticky top-0 z-30 border-b ${wrapperClass}`}>
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 py-4 lg:px-8">
        <Link to={homeHref} className="flex min-w-0 items-center gap-3">
          <div className={`flex h-10 w-10 items-center justify-center rounded-2xl ${brandIconClass}`}>
            <Sparkles size={18} />
          </div>
          <div className="min-w-0">
            <p className="font-display text-base font-semibold tracking-tight">aidCMO</p>
            <p className={`truncate text-xs font-semibold ${brandMetaClass}`}>
              {CONTACT_EMAIL}
            </p>
          </div>
        </Link>

        <nav className="hidden items-center gap-6 lg:flex">
          {items.map((item) => (
            <PublicNavLink
              key={`${item.href}:${item.label}`}
              href={publicHref(item.href)}
              label={t(item.label)}
              className={navClass}
            />
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <button
            onClick={nextLocale}
            className={`rounded-full border px-3 py-2 text-xs font-semibold transition-colors ${localeClass}`}
          >
            {isPublicRoute ? LOCALE_LABELS[seoLocale] : LOCALE_LABELS[locale]}
          </button>
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className={`hidden items-center rounded-full px-4 py-2.5 text-sm font-semibold transition-colors md:inline-flex ${workspaceClass}`}
          >
            {CONTACT_EMAIL}
          </a>
          <a
            href={GITHUB_REPO}
            target="_blank"
            rel="noopener noreferrer"
            className={`hidden items-center gap-2 rounded-full border px-4 py-2.5 text-sm font-semibold transition-colors sm:inline-flex ${githubClass}`}
          >
            {t("siteFooter.sourceCode")}
            <ExternalLink size={14} />
          </a>
          <Link
            to="/workspace"
            className={`inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-semibold transition-colors ${workspaceClass}`}
          >
            <LayoutDashboard size={16} />
            {t("landing.workspaceCta")}
          </Link>
        </div>
      </div>
    </header>
  );
}

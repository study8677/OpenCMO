import type { Locale } from "../i18n";

export type SeoLocale = "en" | "zh";

export const SEO_LOCALES: SeoLocale[] = ["en", "zh"];

const SEO_LOCALE_SET = new Set<SeoLocale>(SEO_LOCALES);

function normalizePath(path: string) {
  const [pathname] = path.split(/[?#]/, 1);
  if (!pathname || pathname === "/") {
    return "/";
  }
  const trimmed = pathname.replace(/^\/+|\/+$/g, "");
  return trimmed ? `/${trimmed}` : "/";
}

export function isSeoLocale(value: string | null | undefined): value is SeoLocale {
  return value != null && SEO_LOCALE_SET.has(value as SeoLocale);
}

export function getSeoLocaleFromLocale(locale: Locale): SeoLocale {
  return locale === "zh" ? "zh" : "en";
}

export function getLocalizedPublicPath(path: string, locale: SeoLocale) {
  const normalized = normalizePath(path);
  return normalized === "/" ? `/${locale}` : `/${locale}${normalized}`;
}

export function stripPublicLocalePrefix(pathname: string) {
  const normalized = normalizePath(pathname);
  const segments = normalized.split("/").filter(Boolean);
  const first = segments[0];

  if (isSeoLocale(first)) {
    const remainder = segments.slice(1).join("/");
    return {
      routeLocale: first,
      barePath: remainder ? `/${remainder}` : "/",
    };
  }

  return {
    routeLocale: null,
    barePath: normalized,
  };
}

export function isPublicRoutePath(pathname: string) {
  const { barePath } = stripPublicLocalePrefix(pathname);
  if (
    barePath === "/"
    || barePath === "/blog"
    || barePath === "/sample-audit"
    || barePath === "/b2b-leads"
    || barePath === "/seo-geo"
    || barePath === "/open-source"
    || barePath === "/sample-data"
    || barePath === "/contact"
    || barePath === "/data-policy"
  ) {
    return true;
  }
  return /^\/blog\/[^/]+$/.test(barePath);
}

export function getLocalizedCurrentPublicPath(pathname: string, locale: SeoLocale) {
  if (!isPublicRoutePath(pathname)) {
    return null;
  }
  const { barePath } = stripPublicLocalePrefix(pathname);
  return getLocalizedPublicPath(barePath, locale);
}

export function getPublicAlternatePaths(path: string) {
  const normalized = normalizePath(path);
  return [
    { hrefLang: "x-default", path: normalized },
    { hrefLang: "en", path: getLocalizedPublicPath(normalized, "en") },
    { hrefLang: "zh-CN", path: getLocalizedPublicPath(normalized, "zh") },
  ];
}

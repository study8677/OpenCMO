export type Locale = "en" | "zh" | "ja" | "ko" | "es";

export const SUPPORTED_LOCALES: Locale[] = ["en", "zh", "ja", "ko", "es"];

export const LOCALE_LABELS: Record<Locale, string> = {
  en: "EN",
  zh: "中文",
  ja: "日本語",
  ko: "한국어",
  es: "ES",
};

const BROWSER_LOCALE_MAP: Array<[prefix: string, locale: Locale]> = [
  ["zh", "zh"],
  ["ja", "ja"],
  ["ko", "ko"],
  ["es", "es"],
  ["en", "en"],
];

export function isLocale(value: string | null | undefined): value is Locale {
  return value != null && SUPPORTED_LOCALES.includes(value as Locale);
}

export function normalizeLocale(value: string | null | undefined): Locale {
  if (!value) return "en";
  const normalized = value.trim().toLowerCase();
  if (isLocale(normalized)) return normalized;
  const matched = BROWSER_LOCALE_MAP.find(([prefix]) => normalized.startsWith(prefix));
  return matched?.[1] ?? "en";
}

export function getDocumentLanguage(locale: Locale): string {
  switch (locale) {
    case "zh":
      return "zh-CN";
    case "ja":
      return "ja";
    case "ko":
      return "ko";
    case "es":
      return "es";
    case "en":
    default:
      return "en";
  }
}

export function resolveLocaleText<T extends string>(
  locale: Locale,
  values: Partial<Record<Locale, T>> & { en: T },
): T {
  return values[locale] ?? values.en;
}

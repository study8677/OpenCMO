import { useLayoutEffect, type ReactNode } from "react";
import { useI18n } from "../../i18n";
import type { SeoLocale } from "../../utils/publicRoutes";

export function PublicLocaleSync({
  locale,
  children,
}: {
  locale: SeoLocale;
  children: ReactNode;
}) {
  const { locale: activeLocale, setLocale } = useI18n();

  useLayoutEffect(() => {
    if (activeLocale !== locale) {
      setLocale(locale);
    }
  }, [activeLocale, locale, setLocale]);

  return activeLocale === locale ? <>{children}</> : null;
}

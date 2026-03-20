import { createContext, useState, useCallback, type ReactNode } from "react";
import { en, type TranslationKey } from "./locales/en";
import { zh } from "./locales/zh";

export type Locale = "en" | "zh";

const dictionaries: Record<Locale, Record<TranslationKey, string>> = { en, zh };

function getInitialLocale(): Locale {
  const stored = localStorage.getItem("opencmo_lang");
  if (stored === "en" || stored === "zh") return stored;
  return navigator.language.startsWith("zh") ? "zh" : "en";
}

export interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}

export const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("opencmo_lang", l);
  }, []);

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>) => {
      let text: string = dictionaries[locale][key];
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          text = text.replaceAll(`{{${k}}}`, String(v));
        }
      }
      return text;
    },
    [locale],
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

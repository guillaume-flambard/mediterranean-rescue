import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { en, type MessageKey, type Messages } from "./en";
import { fr } from "./fr";
import {
  DEFAULT_LOCALE,
  formatDate,
  formatMessage,
  isLocale,
  type Locale,
  type Params,
} from "./format";

const CATALOGS: Readonly<Record<Locale, Messages>> = { en, fr };
const STORAGE_KEY = "locale";

function savedLocale(): Locale {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return isLocale(value) ? value : DEFAULT_LOCALE;
  } catch {
    // Storage can be blocked (private mode, policies): fall back to the default.
    return DEFAULT_LOCALE;
  }
}

export interface I18n {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: MessageKey, params?: Params) => string;
  date: (isoDate: string, style?: "medium" | "long") => string;
  number: (value: number) => string;
}

export function createI18n(locale: Locale, setLocale: (locale: Locale) => void = () => {}): I18n {
  const catalog = CATALOGS[locale];
  return {
    locale,
    setLocale,
    t: (key, params) => {
      const message = catalog[key] as Messages[MessageKey] | undefined;
      // A value outside the catalog (e.g. a new server enum) shows its key, never a crash.
      return message === undefined ? String(key) : formatMessage(locale, message, params);
    },
    date: (isoDate, style) => formatDate(locale, isoDate, style),
    number: (value) => new Intl.NumberFormat(locale).format(value),
  };
}

const I18nContext = createContext<I18n | null>(null);

export function I18nProvider({ children, initialLocale }: { children: ReactNode; initialLocale?: Locale }) {
  const [locale, setLocaleState] = useState<Locale>(() => initialLocale ?? savedLocale());

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = (next: Locale) => {
    setLocaleState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // The choice still applies for this visit.
    }
  };

  return <I18nContext value={createI18n(locale, setLocale)}>{children}</I18nContext>;
}

export function useI18n(): I18n {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n must be used inside I18nProvider");
  return value;
}

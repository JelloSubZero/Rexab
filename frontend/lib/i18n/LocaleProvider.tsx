"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { en } from "@/lib/i18n/dictionaries/en";
import { ru } from "@/lib/i18n/dictionaries/ru";
import type { Locale, Vars } from "@/lib/i18n/types";

const STORAGE_KEY = "rexab_locale";

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, vars?: Vars) => string;
  tList: (key: string) => string[];
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function detectLocale(): Locale {
  if (
    typeof navigator !== "undefined" &&
    navigator.language.toLowerCase().startsWith("ru")
  ) {
    return "ru";
  }
  return "en";
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    const resolved: Locale =
      stored === "en" || stored === "ru" ? stored : detectLocale();

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLocaleState(resolved);

    if (!stored) localStorage.setItem(STORAGE_KEY, resolved);
  }, []);

  const setLocale = useCallback((next: Locale) => {
    localStorage.setItem(STORAGE_KEY, next);
    setLocaleState(next);
  }, []);

  const t = useCallback(
    (key: string, vars: Vars = {}) => {
      const dict = locale === "ru" ? ru : en;
      const entry = dict[key];

      if (entry === undefined) {
        if (process.env.NODE_ENV !== "production") {
          console.warn(`Missing translation for key "${key}"`);
        }
        return key;
      }

      if (typeof entry === "function") return entry(vars);

      if (Array.isArray(entry)) {
        if (process.env.NODE_ENV !== "production") {
          console.warn(`Key "${key}" is a list; use tList() instead of t()`);
        }
        return key;
      }

      return entry;
    },
    [locale],
  );

  const tList = useCallback(
    (key: string) => {
      const dict = locale === "ru" ? ru : en;
      const entry = dict[key];

      if (Array.isArray(entry)) return entry;

      if (process.env.NODE_ENV !== "production") {
        console.warn(`Missing or non-list translation for key "${key}"`);
      }
      return [];
    },
    [locale],
  );

  if (locale === null) return null;

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t, tList }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useTranslation(): LocaleContextValue {
  const context = useContext(LocaleContext);

  if (!context) {
    throw new Error("useTranslation must be used within a LocaleProvider");
  }

  return context;
}

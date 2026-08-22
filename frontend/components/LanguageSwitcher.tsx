"use client";

import { useTranslation } from "@/lib/i18n/LocaleProvider";
import { clsx } from "@/lib/clsx";
import type { Locale } from "@/lib/i18n/types";

interface LanguageSwitcherProps {
  variant?: "light" | "dark";
}

const OPTIONS: { locale: Locale; label: string }[] = [
  { locale: "en", label: "EN" },
  { locale: "ru", label: "RU" },
];

export function LanguageSwitcher({ variant = "light" }: LanguageSwitcherProps) {
  const { locale, setLocale } = useTranslation();

  return (
    <div
      className={clsx(
        "flex items-center gap-0.5 rounded-lg border p-0.5 text-xs font-medium",
        variant === "dark" ? "border-white/15 bg-white/5" : "border-border bg-card",
      )}
    >
      {OPTIONS.map((option) => (
        <button
          key={option.locale}
          type="button"
          onClick={() => setLocale(option.locale)}
          aria-pressed={locale === option.locale}
          className={clsx(
            "rounded-md px-2 py-1 transition-colors",
            locale === option.locale
              ? "bg-accent text-white"
              : variant === "dark"
                ? "text-dark-muted hover:text-white"
                : "text-secondary hover:text-primary",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

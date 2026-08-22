"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { clsx } from "@/lib/clsx";
import { Container } from "@/components/ui/Container";
import { useTranslation } from "@/lib/i18n/LocaleProvider";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export function Navbar() {
  const { t } = useTranslation();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const links = [
    { href: "#how-it-works", label: t("landing.nav.howItWorks") },
    { href: "#features", label: t("landing.nav.features") },
    { href: "#use-cases", label: t("landing.nav.useCases") },
  ];

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > window.innerHeight * 0.6);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const light = isScrolled || isMenuOpen;

  return (
    <header
      className={clsx(
        "fixed inset-x-0 top-0 z-50 transition-colors duration-300",
        light
          ? "border-b border-border bg-card/90 backdrop-blur-md"
          : "border-b border-white/10 bg-transparent",
      )}
    >
      <Container className="flex h-16 items-center justify-between">
        <Link
          href="/"
          className={clsx(
            "flex items-center gap-2 text-lg font-semibold tracking-tight",
            light ? "text-primary" : "text-white",
          )}
        >
          <span
            className="flex h-6 w-6 items-center justify-center rounded-md bg-accent text-xs font-bold text-white"
            aria-hidden="true"
          >
            R
          </span>
          REXAB
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className={clsx(
                "text-sm font-medium transition-colors",
                light
                  ? "text-secondary hover:text-primary"
                  : "text-dark-muted hover:text-white",
              )}
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-4 md:flex">
          <Link
            href="/login"
            className={clsx(
              "text-sm font-medium transition-colors",
              light
                ? "text-secondary hover:text-primary"
                : "text-dark-muted hover:text-white",
            )}
          >
            {t("landing.nav.login")}
          </Link>
          <LanguageSwitcher variant={light ? "light" : "dark"} />
          <Link
            href="/register"
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-all hover:-translate-y-px hover:bg-accent-hover active:scale-[0.98]"
          >
            {t("landing.cta.getStarted")}
          </Link>
        </div>

        <button
          onClick={() => setIsMenuOpen((open) => !open)}
          className={clsx(
            "rounded-md p-2 md:hidden",
            light ? "text-primary" : "text-white",
          )}
          aria-label={isMenuOpen ? t("landing.nav.closeMenu") : t("landing.nav.openMenu")}
          aria-expanded={isMenuOpen}
        >
          {isMenuOpen ? (
            <X className="h-5 w-5" aria-hidden="true" />
          ) : (
            <Menu className="h-5 w-5" aria-hidden="true" />
          )}
        </button>
      </Container>

      {isMenuOpen && (
        <div className="border-t border-border bg-card px-6 py-4 md:hidden">
          <nav className="flex flex-col gap-4">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setIsMenuOpen(false)}
                className="text-sm font-medium text-secondary hover:text-primary"
              >
                {link.label}
              </a>
            ))}
            <Link
              href="/login"
              onClick={() => setIsMenuOpen(false)}
              className="text-sm font-medium text-secondary hover:text-primary"
            >
              {t("landing.nav.login")}
            </Link>
            <Link
              href="/register"
              onClick={() => setIsMenuOpen(false)}
              className="rounded-lg bg-accent px-4 py-2.5 text-center text-sm font-medium text-white"
            >
              {t("landing.cta.getStarted")}
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}

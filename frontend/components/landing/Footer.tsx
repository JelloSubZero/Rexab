"use client";

import Link from "next/link";
import { Container } from "@/components/ui/Container";
import { useTranslation } from "@/lib/i18n/LocaleProvider";

export function Footer() {
  const { t } = useTranslation();

  const columns = [
    {
      title: t("landing.footer.columns.product"),
      links: [
        { label: t("landing.nav.howItWorks"), href: "#how-it-works" },
        { label: t("landing.nav.features"), href: "#features" },
        { label: t("landing.nav.useCases"), href: "#use-cases" },
      ],
    },
    {
      title: t("landing.footer.columns.resources"),
      links: [
        { label: t("landing.footer.links.help"), href: "#" },
        { label: t("landing.footer.links.documentation"), href: "#" },
      ],
    },
    {
      title: t("landing.footer.columns.company"),
      links: [
        { label: t("landing.footer.links.about"), href: "#" },
        { label: t("landing.footer.links.contact"), href: "#" },
      ],
    },
    {
      title: t("landing.footer.columns.legal"),
      links: [
        { label: t("landing.footer.links.privacy"), href: "#" },
        { label: t("landing.footer.links.terms"), href: "#" },
      ],
    },
  ];

  return (
    <footer className="border-t border-border bg-card py-16">
      <Container>
        <div className="grid grid-cols-2 gap-10 sm:grid-cols-3 lg:grid-cols-5">
          <div className="col-span-2 lg:col-span-1">
            <Link
              href="/"
              className="flex items-center gap-2 text-lg font-semibold tracking-tight text-primary"
            >
              <span
                className="flex h-6 w-6 items-center justify-center rounded-md bg-accent text-xs font-bold text-white"
                aria-hidden="true"
              >
                R
              </span>
              REXAB
            </Link>
            <p className="mt-3 text-sm text-secondary">
              {t("landing.footer.tagline")}
            </p>
          </div>

          {columns.map((column) => (
            <nav key={column.title} aria-label={column.title}>
              <h3 className="text-sm font-semibold text-primary">
                {column.title}
              </h3>
              <ul className="mt-3 flex flex-col gap-2.5">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-secondary transition-colors hover:text-primary"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <div className="mt-12 border-t border-border pt-6 text-sm text-secondary">
          © 2026 Rexab
        </div>
      </Container>
    </footer>
  );
}

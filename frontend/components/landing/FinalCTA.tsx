"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { FadeIn } from "@/components/landing/FadeIn";
import { useTranslation } from "@/lib/i18n/LocaleProvider";

export function FinalCTA() {
  const { t } = useTranslation();

  return (
    <section className="relative overflow-hidden bg-dark py-24 sm:py-32">
      <div
        className="pointer-events-none absolute left-1/2 top-0 h-64 w-64 -translate-x-1/2 rounded-full bg-accent/20 blur-3xl"
        aria-hidden="true"
      />

      <Container className="relative text-center">
        <FadeIn>
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            {t("landing.finalCta.title")}
          </h2>
          <p className="mx-auto mt-4 max-w-md text-lg text-dark-muted">
            {t("landing.finalCta.subtitle")}
          </p>
          <Link
            href="/register"
            className="mt-8 inline-flex items-center gap-2 rounded-lg bg-accent px-6 py-3.5 text-sm font-medium text-white transition-all hover:-translate-y-px hover:bg-accent-hover active:scale-[0.98]"
          >
            {t("landing.cta.getStarted")}
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </FadeIn>
      </Container>
    </section>
  );
}

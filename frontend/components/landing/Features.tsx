"use client";

import { Receipt, Users, CheckCircle2, LayoutDashboard } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { FadeIn } from "@/components/landing/FadeIn";
import { useTranslation } from "@/lib/i18n/LocaleProvider";

export function Features() {
  const { t } = useTranslation();

  const expenseTags = [
    { key: "landing.demo.payments.dinner", amount: "80 zł" },
    { key: "landing.demo.payments.groceries", amount: "120 zł" },
    { key: "landing.demo.payments.internet", amount: "40 zł" },
  ];

  return (
    <section id="features" className="bg-card py-24 sm:py-32">
      <Container>
        <FadeIn className="mx-auto max-w-xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
            {t("landing.features.title")}
          </h2>
        </FadeIn>

        <div className="mt-16 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <FadeIn delay={0} className="sm:col-span-2">
            <div className="rounded-2xl border border-border bg-bg p-8">
              <Receipt
                className="h-6 w-6 text-accent"
                aria-hidden="true"
              />
              <h3 className="mt-4 text-xl font-semibold text-primary">
                {t("landing.features.shared.title")}
              </h3>
              <p className="mt-2 max-w-md text-secondary">
                {t("landing.features.shared.description")}
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                {expenseTags.map((tag) => (
                  <span
                    key={tag.key}
                    className="rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-secondary"
                  >
                    {t(tag.key)} · {tag.amount}
                  </span>
                ))}
              </div>
            </div>
          </FadeIn>

          <FadeIn delay={0.1}>
            <div className="h-full rounded-2xl border border-border bg-bg p-8">
              <Users className="h-6 w-6 text-accent" aria-hidden="true" />
              <h3 className="mt-4 text-xl font-semibold text-primary">
                {t("landing.features.group.title")}
              </h3>
              <p className="mt-2 text-secondary">
                {t("landing.features.group.description")}
              </p>
            </div>
          </FadeIn>

          <FadeIn delay={0.15}>
            <div className="h-full rounded-2xl border border-border bg-bg p-8">
              <CheckCircle2
                className="h-6 w-6 text-accent"
                aria-hidden="true"
              />
              <h3 className="mt-4 text-xl font-semibold text-primary">
                {t("landing.features.settlements.title")}
              </h3>
              <p className="mt-2 text-secondary">
                {t("landing.features.settlements.description")}
              </p>
            </div>
          </FadeIn>

          <FadeIn delay={0.2} className="sm:col-span-2">
            <div className="rounded-2xl border border-border bg-bg p-8">
              <LayoutDashboard
                className="h-6 w-6 text-accent"
                aria-hidden="true"
              />
              <h3 className="mt-4 text-xl font-semibold text-primary">
                {t("landing.features.overview.title")}
              </h3>
              <p className="mt-2 max-w-md text-secondary">
                {t("landing.features.overview.description")}
              </p>
            </div>
          </FadeIn>
        </div>
      </Container>
    </section>
  );
}

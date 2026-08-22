"use client";

import { Container } from "@/components/ui/Container";
import { FadeIn } from "@/components/landing/FadeIn";
import { useTranslation } from "@/lib/i18n/LocaleProvider";
import {
  demoMemberBalances,
  demoMembers,
  demoTotalExpenses,
} from "@/components/landing/mock-data";

export function ProductShowcase() {
  const { t } = useTranslation();

  return (
    <section className="bg-bg py-24 sm:py-32">
      <Container className="grid grid-cols-1 items-center gap-16 lg:grid-cols-2">
        <FadeIn>
          <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
            {t("landing.showcase.title")}
          </h2>
          <p className="mt-4 max-w-md text-lg leading-relaxed text-secondary">
            {t("landing.showcase.subtitle")}
          </p>
        </FadeIn>

        <FadeIn delay={0.15}>
          <div className="rounded-2xl border border-border bg-card p-6 shadow-lg">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-primary">{t("landing.demo.roomName")}</p>
              <span className="rounded-full bg-positive-bg px-2.5 py-1 text-xs font-medium text-positive">
                {t("landing.demo.status.active")}
              </span>
            </div>

            <p className="mt-5 text-xs font-medium uppercase tracking-wide text-secondary">
              {t("landing.showcase.totalExpenses")}
            </p>
            <p className="mt-1 text-3xl font-semibold text-primary">
              {demoTotalExpenses.toLocaleString()} zł
            </p>

            <div className="my-5 h-px bg-border" />

            <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
              {t("member.list.title")}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {demoMembers.map((member) => (
                <span
                  key={member}
                  className="rounded-full border border-border bg-bg px-3 py-1 text-sm text-primary"
                >
                  {member}
                </span>
              ))}
            </div>

            <div className="my-5 h-px bg-border" />

            <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
              {t("stats.balance")}
            </p>
            <div className="mt-3 flex flex-col gap-2.5">
              {demoMemberBalances.map((member) => (
                <div
                  key={member.name}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-primary">{member.name}</span>
                  <span
                    className={
                      member.balance > 0
                        ? "font-medium text-positive"
                        : "font-medium text-negative"
                    }
                  >
                    {member.balance > 0 ? "+" : ""}
                    {member.balance} zł
                  </span>
                </div>
              ))}
            </div>
          </div>
        </FadeIn>
      </Container>
    </section>
  );
}

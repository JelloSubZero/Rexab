"use client";

import { Home, Plane, Users } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { FadeIn } from "@/components/landing/FadeIn";
import { useTranslation } from "@/lib/i18n/LocaleProvider";

export function UseCases() {
  const { t, tList } = useTranslation();

  const useCases = [
    {
      icon: Home,
      title: t("landing.useCases.roommates.title"),
      items: tList("landing.useCases.roommates.items"),
    },
    {
      icon: Plane,
      title: t("landing.useCases.trips.title"),
      items: tList("landing.useCases.trips.items"),
    },
    {
      icon: Users,
      title: t("landing.useCases.groups.title"),
      items: tList("landing.useCases.groups.items"),
    },
  ];

  return (
    <section id="use-cases" className="bg-bg py-24 sm:py-32">
      <Container>
        <FadeIn className="mx-auto max-w-xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
            {t("landing.useCases.title")}
          </h2>
        </FadeIn>

        <div className="mt-16 grid grid-cols-1 gap-5 sm:grid-cols-3">
          {useCases.map((useCase, index) => {
            const Icon = useCase.icon;
            return (
              <FadeIn key={useCase.title} delay={index * 0.12}>
                <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-7">
                  <div
                    className="pointer-events-none absolute -right-8 -top-8 h-28 w-28 rounded-full bg-accent/5"
                    aria-hidden="true"
                  />
                  <div className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10 text-accent">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <h3 className="relative mt-5 text-lg font-semibold text-primary">
                    {useCase.title}
                  </h3>
                  <ul className="relative mt-3 flex flex-col gap-1.5 text-sm text-secondary">
                    {useCase.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </FadeIn>
            );
          })}
        </div>
      </Container>
    </section>
  );
}

"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Sparkle } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { Badge } from "@/components/ui/Badge";
import { HeroDashboard } from "@/components/landing/HeroDashboard";
import { useTranslation } from "@/lib/i18n/LocaleProvider";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

export function Hero() {
  const { t } = useTranslation();

  return (
    <section className="relative overflow-hidden bg-dark pt-32 pb-24 lg:min-h-[92vh] lg:pt-40">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(60% 50% at 20% 20%, rgba(99,102,241,0.16), transparent 60%), radial-gradient(45% 40% at 85% 15%, rgba(99,102,241,0.10), transparent 55%)",
        }}
        aria-hidden="true"
      />

      <Container className="relative grid grid-cols-1 items-center gap-16 lg:grid-cols-2">
        <div>
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={{ duration: 0.6 }}
          >
            <Badge tone="dark">
              <Sparkle className="h-3 w-3 text-accent" aria-hidden="true" />
              {t("landing.hero.badge")}
            </Badge>
          </motion.div>

          <motion.h1
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={{ duration: 0.65, delay: 0.1 }}
            className="mt-6 text-[40px] font-semibold leading-[1.05] tracking-tight text-white sm:text-[52px] lg:text-[68px]"
          >
            {t("landing.hero.headline")}
            <br />
            {t("landing.hero.headlineSuffix")}{" "}
            <span className="text-accent">{t("landing.hero.headlineAccent")}</span>
          </motion.h1>

          <motion.p
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={{ duration: 0.65, delay: 0.2 }}
            className="mt-6 max-w-[520px] text-lg leading-relaxed text-dark-muted"
          >
            {t("landing.hero.subtitle")}
          </motion.p>

          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={{ duration: 0.65, delay: 0.3 }}
            className="mt-9 flex flex-wrap items-center gap-4"
          >
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-3 text-sm font-medium text-white transition-all hover:-translate-y-px hover:bg-accent-hover active:scale-[0.98]"
            >
              {t("landing.cta.getStarted")}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center gap-2 rounded-lg border border-white/15 px-5 py-3 text-sm font-medium text-white transition-all hover:-translate-y-px hover:border-white/30 active:scale-[0.98]"
            >
              {t("landing.hero.seeHowItWorks")}
            </a>
          </motion.div>
        </div>

        <HeroDashboard />
      </Container>
    </section>
  );
}

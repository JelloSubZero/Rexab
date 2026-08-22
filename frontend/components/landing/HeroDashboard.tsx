"use client";

import { motion, useReducedMotion } from "framer-motion";
import { MoreHorizontal, Plus } from "lucide-react";
import { AnimatedNumber } from "@/components/landing/AnimatedNumber";
import { useTranslation } from "@/lib/i18n/LocaleProvider";
import {
  demoBalance,
  demoPayments,
  demoTransfers,
} from "@/components/landing/mock-data";

function FloatingCard({
  className,
  delay,
  duration,
  children,
}: {
  className: string;
  delay: number;
  duration: number;
  children: React.ReactNode;
}) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      className={`absolute hidden rounded-xl border border-border bg-card px-4 py-3 text-left shadow-lg lg:block ${className}`}
      initial={{ opacity: 0, y: 10 }}
      animate={
        prefersReducedMotion
          ? { opacity: 1, y: 0 }
          : { opacity: 1, y: [0, -10, 0] }
      }
      transition={
        prefersReducedMotion
          ? { duration: 0.6, delay }
          : {
              opacity: { duration: 0.6, delay },
              y: { duration, repeat: Infinity, ease: "easeInOut", delay },
            }
      }
    >
      {children}
    </motion.div>
  );
}

export function HeroDashboard() {
  const { t } = useTranslation();
  const dinner = demoPayments[0];

  return (
    <div className="relative mx-auto w-full max-w-md lg:mx-0">
      <motion.div
        initial={{ opacity: 0, scale: 0.94, rotateX: 4, rotateY: -6 }}
        animate={{ opacity: 1, scale: 1, rotateX: 4, rotateY: -6 }}
        transition={{ duration: 0.7, delay: 0.5, ease: "easeOut" }}
        style={{ perspective: 1200 }}
        className="relative rounded-2xl border border-white/10 bg-card p-6 shadow-2xl"
      >
        <div className="flex items-center justify-between">
          <p className="font-semibold text-primary">{t("landing.demo.roomName")}</p>
          <MoreHorizontal
            className="h-4 w-4 text-secondary"
            aria-hidden="true"
          />
        </div>

        <p className="mt-5 text-xs font-medium uppercase tracking-wide text-secondary">
          {t("landing.heroDashboard.yourBalance")}
        </p>
        <p className="mt-1 text-4xl font-semibold text-positive">
          <AnimatedNumber value={demoBalance.balance} prefix="+" suffix=" zł" />
        </p>

        <div className="my-5 h-px bg-border" />

        <div className="flex flex-col gap-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-secondary">{t("stats.youOwe")}</span>
            <span className="font-medium text-primary">
              {demoBalance.youOwe} zł
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-secondary">{t("stats.owedToYou")}</span>
            <span className="font-medium text-primary">
              {demoBalance.youAreOwed} zł
            </span>
          </div>
        </div>

        <div className="my-5 h-px bg-border" />

        <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
          {t("whoOwesWhom.title")}
        </p>
        <div className="mt-3 flex flex-col gap-2.5">
          {demoTransfers.map((transfer) => (
            <div
              key={`${transfer.from}-${transfer.to}`}
              className="flex items-center justify-between text-sm"
            >
              <span className="text-primary">
                {transfer.from === "You" ? t("landing.demo.you") : transfer.from}{" "}
                <span className="text-secondary">→</span>{" "}
                {transfer.to === "You" ? t("landing.demo.you") : transfer.to}
              </span>
              <span className="font-medium text-primary">
                {transfer.amount} zł
              </span>
            </div>
          ))}
        </div>

        <div className="my-5 h-px bg-border" />

        <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
          {t("landing.heroDashboard.recentPayment")}
        </p>
        <div className="mt-2 flex items-center justify-between text-sm">
          <span className="text-primary">
            {dinner.emoji} {t(dinner.labelKey)}
          </span>
          <span className="font-medium text-primary">
            {dinner.amount} zł
          </span>
        </div>

        <button className="mt-5 flex w-full items-center justify-center gap-1.5 rounded-lg border border-border py-2.5 text-sm font-medium text-primary transition-colors hover:bg-bg">
          <Plus className="h-4 w-4" aria-hidden="true" />
          {t("room.actions.addPayment")}
        </button>
      </motion.div>

      <FloatingCard
        className="-left-10 top-6 -rotate-3"
        delay={1.1}
        duration={7}
      >
        <p className="text-[11px] font-medium uppercase tracking-wide text-secondary">
          {t("landing.heroDashboard.youAreOwed")}
        </p>
        <p className="text-lg font-semibold text-positive">+230 zł</p>
      </FloatingCard>

      <FloatingCard
        className="-right-8 top-1/3 rotate-2"
        delay={1.3}
        duration={8}
      >
        <p className="text-sm font-medium text-primary">
          {t("landing.heroDashboard.settlementConfirmed")}
        </p>
      </FloatingCard>

      <FloatingCard
        className="-left-6 bottom-2 rotate-1"
        delay={1.5}
        duration={6.5}
      >
        <p className="text-sm text-primary">
          <span className="font-medium">Alex</span> {t("common.paidWord")}
        </p>
        <p className="text-sm font-semibold text-primary">50 zł</p>
      </FloatingCard>
    </div>
  );
}

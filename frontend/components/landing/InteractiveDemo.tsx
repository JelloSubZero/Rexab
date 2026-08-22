"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Container } from "@/components/ui/Container";
import { FadeIn } from "@/components/landing/FadeIn";
import { clsx } from "@/lib/clsx";
import { useTranslation } from "@/lib/i18n/LocaleProvider";
import {
  demoBalance,
  demoMembers,
  demoPayments,
  demoSettlements,
} from "@/components/landing/mock-data";

type TabId = "balance" | "expenses" | "members" | "settlements";

function BalanceTab() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center gap-6 py-6 text-center">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-secondary">
          {t("stats.balance")}
        </p>
        <p className="mt-1 text-4xl font-semibold text-positive">
          +{demoBalance.balance} zł
        </p>
      </div>
      <div className="flex gap-10">
        <div>
          <p className="text-xs text-secondary">{t("stats.youOwe")}</p>
          <p className="mt-1 font-semibold text-primary">
            {demoBalance.youOwe} zł
          </p>
        </div>
        <div>
          <p className="text-xs text-secondary">{t("stats.owedToYou")}</p>
          <p className="mt-1 font-semibold text-primary">
            {demoBalance.youAreOwed} zł
          </p>
        </div>
      </div>
    </div>
  );
}

function ExpensesTab() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-2 py-2">
      {demoPayments.map((payment) => (
        <div
          key={payment.labelKey}
          className="flex items-center justify-between rounded-lg bg-bg px-4 py-3 text-sm"
        >
          <span className="text-primary">
            {payment.emoji} {t(payment.labelKey)}
          </span>
          <span className="font-medium text-primary">
            {payment.amount} zł
          </span>
        </div>
      ))}
    </div>
  );
}

function MembersTab() {
  return (
    <div className="flex flex-wrap justify-center gap-3 py-6">
      {demoMembers.map((member) => (
        <div
          key={member}
          className="flex items-center gap-2 rounded-full border border-border bg-bg px-4 py-2 text-sm text-primary"
        >
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent/10 text-xs font-semibold text-accent">
            {member.charAt(0)}
          </span>
          {member}
        </div>
      ))}
    </div>
  );
}

function SettlementsTab() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-2 py-2">
      {demoSettlements.map((settlement) => (
        <div
          key={`${settlement.from}-${settlement.to}`}
          className="flex items-center justify-between rounded-lg bg-bg px-4 py-3 text-sm"
        >
          <span className="text-primary">
            <span className="font-medium">
              {settlement.from === "You" ? t("landing.demo.you") : settlement.from}
            </span>{" "}
            <span className="text-secondary">→</span>{" "}
            <span className="font-medium">
              {settlement.to === "You" ? t("landing.demo.you") : settlement.to}
            </span>
          </span>
          <div className="flex items-center gap-3">
            <span className="font-medium text-primary">
              {settlement.amount} zł
            </span>
            <span
              className={clsx(
                "rounded-full px-2.5 py-1 text-xs font-medium",
                settlement.status === "confirmed"
                  ? "bg-positive-bg text-positive"
                  : "bg-warning-bg text-warning",
              )}
            >
              {settlement.status === "confirmed"
                ? t("landing.demo.status.confirmed")
                : t("landing.demo.status.pending")}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

const TAB_CONTENT: Record<TabId, React.ComponentType> = {
  balance: BalanceTab,
  expenses: ExpensesTab,
  members: MembersTab,
  settlements: SettlementsTab,
};

export function InteractiveDemo() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabId>("balance");
  const ActiveContent = TAB_CONTENT[activeTab];

  const tabs: { id: TabId; label: string }[] = [
    { id: "balance", label: t("stats.balance") },
    { id: "expenses", label: t("landing.demo.tabs.expenses") },
    { id: "members", label: t("member.list.title") },
    { id: "settlements", label: t("settlement.list.title") },
  ];

  return (
    <section className="bg-card py-24 sm:py-32">
      <Container>
        <FadeIn className="mx-auto max-w-xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
            {t("landing.demo.title")}
          </h2>
          <p className="mt-4 text-lg text-secondary">
            {t("landing.demo.subtitle")}
          </p>
        </FadeIn>

        <FadeIn delay={0.15} className="mx-auto mt-12 max-w-xl">
          <div className="flex gap-1 overflow-x-auto rounded-xl border border-border bg-bg p-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  "flex-1 whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-medium transition-colors",
                  activeTab === tab.id
                    ? "bg-card text-primary shadow-sm"
                    : "text-secondary hover:text-primary",
                )}
                aria-pressed={activeTab === tab.id}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="mt-4 min-h-[220px] rounded-2xl border border-border bg-card px-6 shadow-sm">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
              >
                <ActiveContent />
              </motion.div>
            </AnimatePresence>
          </div>
        </FadeIn>
      </Container>
    </section>
  );
}

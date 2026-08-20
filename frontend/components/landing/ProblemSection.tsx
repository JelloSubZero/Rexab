"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { FadeIn } from "@/components/landing/FadeIn";

const chaosItems = [
  { label: "Alex", amount: "120 zł", className: "left-[6%] top-2 rotate-[-4deg]" },
  { label: "Daniel", amount: "30 zł", className: "left-[38%] top-16 rotate-[3deg]" },
  { label: "John", amount: "50 zł", className: "right-[8%] top-0 rotate-[2deg]" },
];

const clearTransfers = [
  { from: "Alex", to: "Daniel", amount: "120 zł" },
  { from: "John", to: "Alex", amount: "50 zł" },
];

export function ProblemSection() {
  return (
    <section className="bg-bg py-24 sm:py-32">
      <Container>
        <FadeIn className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
            Shared expenses shouldn&apos;t be complicated.
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-secondary">
            You paid for dinner. Someone bought groceries. Another person
            paid the rent. And now&nbsp;&mdash; who owes whom?
          </p>
        </FadeIn>

        <div className="mt-16 grid grid-cols-1 items-center gap-6 lg:grid-cols-[1fr_auto_1fr]">
          <FadeIn delay={0.1}>
            <div className="relative h-56 rounded-2xl border border-border bg-card p-6">
              <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
                Without Rexab
              </p>
              <div className="relative mt-4 h-32">
                {chaosItems.map((item) => (
                  <motion.div
                    key={item.label}
                    initial={{ opacity: 0, scale: 0.9 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5 }}
                    className={`absolute rounded-lg border border-border bg-bg px-3 py-2 text-sm shadow-sm ${item.className}`}
                  >
                    <span className="font-medium text-primary">
                      {item.label}
                    </span>{" "}
                    <span className="text-negative">{item.amount}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          </FadeIn>

          <FadeIn delay={0.2} className="flex justify-center">
            <div
              className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/10 text-accent lg:rotate-0"
              aria-hidden="true"
            >
              <ArrowRight className="h-5 w-5 hidden lg:block" />
              <span className="text-xl lg:hidden">↓</span>
            </div>
          </FadeIn>

          <FadeIn delay={0.3}>
            <div className="rounded-2xl border border-accent/20 bg-card p-6 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-accent">
                With Rexab
              </p>
              <div className="mt-4 flex flex-col gap-3">
                {clearTransfers.map((transfer) => (
                  <div
                    key={`${transfer.from}-${transfer.to}`}
                    className="flex items-center justify-between rounded-lg bg-bg px-3.5 py-2.5 text-sm"
                  >
                    <span className="text-primary">
                      <span className="font-medium">{transfer.from}</span>{" "}
                      <span className="text-secondary">→</span>{" "}
                      <span className="font-medium">{transfer.to}</span>
                    </span>
                    <span className="font-semibold text-primary">
                      {transfer.amount}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </FadeIn>
        </div>
      </Container>
    </section>
  );
}

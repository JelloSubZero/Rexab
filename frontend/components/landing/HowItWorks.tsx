import { Home, Receipt, CheckCircle2 } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { FadeIn } from "@/components/landing/FadeIn";

const steps = [
  {
    number: "01",
    icon: Home,
    title: "Create a room",
    description: "Create a space for your apartment, trip or group.",
  },
  {
    number: "02",
    icon: Receipt,
    title: "Add expenses",
    description: "Record who paid and who should share the cost.",
  },
  {
    number: "03",
    icon: CheckCircle2,
    title: "Settle up",
    description: "Rexab calculates who owes whom and tracks repayments.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-card py-24 sm:py-32">
      <Container>
        <FadeIn className="mx-auto max-w-xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
            How Rexab works.
          </h2>
          <p className="mt-4 text-lg text-secondary">
            Three simple steps. No spreadsheets. No calculations.
          </p>
        </FadeIn>

        <div className="relative mt-16 grid grid-cols-1 gap-10 sm:grid-cols-3">
          <div
            className="absolute left-0 right-0 top-6 hidden h-px bg-border sm:block"
            aria-hidden="true"
          />

          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <FadeIn key={step.number} delay={index * 0.12}>
                <div className="relative flex flex-col items-start">
                  <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-full border border-border bg-card text-accent">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <span className="mt-4 text-sm font-semibold text-secondary">
                    {step.number}
                  </span>
                  <h3 className="mt-1 text-lg font-semibold text-primary">
                    {step.title}
                  </h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-secondary">
                    {step.description}
                  </p>
                </div>
              </FadeIn>
            );
          })}
        </div>
      </Container>
    </section>
  );
}

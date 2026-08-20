import { Check } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { FadeIn } from "@/components/landing/FadeIn";

const points = [
  "Clear balances",
  "Transparent settlements",
  "Permission-based actions",
  "One source of truth",
  "Simple group management",
];

export function TrustSection() {
  return (
    <section className="bg-bg py-24 sm:py-32">
      <Container className="mx-auto max-w-2xl text-center">
        <FadeIn>
          <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
            Built around clarity.
          </h2>
        </FadeIn>

        <FadeIn delay={0.1}>
          <ul className="mx-auto mt-10 grid max-w-md grid-cols-1 gap-3 text-left sm:grid-cols-2">
            {points.map((point) => (
              <li
                key={point}
                className="flex items-center gap-2.5 rounded-lg border border-border bg-card px-4 py-3 text-sm text-primary"
              >
                <Check
                  className="h-4 w-4 shrink-0 text-positive"
                  aria-hidden="true"
                />
                {point}
              </li>
            ))}
          </ul>
        </FadeIn>

        <FadeIn delay={0.2}>
          <p className="mx-auto mt-10 max-w-md text-sm text-secondary">
            Every balance-changing action goes through a permission
            check on the server — not the client — before it&apos;s
            applied.
          </p>
        </FadeIn>
      </Container>
    </section>
  );
}

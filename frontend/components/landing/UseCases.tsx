import { Home, Plane, Users } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { FadeIn } from "@/components/landing/FadeIn";

const useCases = [
  {
    icon: Home,
    title: "Roommates",
    items: ["Rent", "Groceries", "Utilities", "Internet"],
  },
  {
    icon: Plane,
    title: "Trips",
    items: ["Hotels", "Food", "Transport", "Tickets"],
  },
  {
    icon: Users,
    title: "Groups",
    items: ["Events", "Parties", "Projects", "Activities"],
  },
];

export function UseCases() {
  return (
    <section id="use-cases" className="bg-bg py-24 sm:py-32">
      <Container>
        <FadeIn className="mx-auto max-w-xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
            Wherever money is shared.
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

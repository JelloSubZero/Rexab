import { Receipt, Users, CheckCircle2, LayoutDashboard } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { FadeIn } from "@/components/landing/FadeIn";

export function Features() {
  return (
    <section id="features" className="bg-card py-24 sm:py-32">
      <Container>
        <FadeIn className="mx-auto max-w-xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
            Everything your group needs.
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
                Shared expenses
              </h3>
              <p className="mt-2 max-w-md text-secondary">
                Track every expense in one place, with who paid and who
                owes what always visible.
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                {["Dinner · 80 zł", "Groceries · 120 zł", "Internet · 40 zł"].map(
                  (item) => (
                    <span
                      key={item}
                      className="rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-secondary"
                    >
                      {item}
                    </span>
                  ),
                )}
              </div>
            </div>
          </FadeIn>

          <FadeIn delay={0.1}>
            <div className="h-full rounded-2xl border border-border bg-bg p-8">
              <Users className="h-6 w-6 text-accent" aria-hidden="true" />
              <h3 className="mt-4 text-xl font-semibold text-primary">
                Group management
              </h3>
              <p className="mt-2 text-secondary">
                Manage members and permissions easily.
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
                Easy settlements
              </h3>
              <p className="mt-2 text-secondary">
                Keep track of who has paid you back.
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
                Clear overview
              </h3>
              <p className="mt-2 max-w-md text-secondary">
                See balances and debts instantly, without digging
                through chat history.
              </p>
            </div>
          </FadeIn>
        </div>
      </Container>
    </section>
  );
}

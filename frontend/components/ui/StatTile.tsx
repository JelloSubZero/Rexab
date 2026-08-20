import { clsx } from "@/lib/clsx";

type Tone = "neutral" | "positive" | "negative";

interface StatTileProps {
  label: string;
  value: string;
  tone?: Tone;
}

const toneClasses: Record<Tone, string> = {
  neutral: "text-primary",
  positive: "text-positive",
  negative: "text-negative",
};

export function StatTile({ label, value, tone = "neutral" }: StatTileProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-secondary">
        {label}
      </p>
      <p className={clsx("mt-2 text-2xl font-semibold", toneClasses[tone])}>
        {value}
      </p>
    </div>
  );
}

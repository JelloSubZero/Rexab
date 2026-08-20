import type { HTMLAttributes } from "react";
import { clsx } from "@/lib/clsx";

type Tone = "light" | "dark";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

const toneClasses: Record<Tone, string> = {
  light: "border-border bg-card text-secondary",
  dark: "border-dark-border bg-white/5 text-dark-muted",
};

export function Badge({ tone = "light", className, ...props }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-xs font-medium",
        toneClasses[tone],
        className,
      )}
      {...props}
    />
  );
}

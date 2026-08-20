import type { HTMLAttributes } from "react";
import { clsx } from "@/lib/clsx";

export function Card({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx(
        "rounded-xl border border-border bg-card p-5 shadow-sm",
        className,
      )}
      {...props}
    />
  );
}

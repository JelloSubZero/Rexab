import { clsx } from "@/lib/clsx";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={clsx("animate-pulse rounded-md bg-border", className)}
      aria-hidden="true"
    />
  );
}

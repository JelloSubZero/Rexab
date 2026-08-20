import type { HTMLAttributes } from "react";
import { clsx } from "@/lib/clsx";

export function Container({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx("mx-auto w-full max-w-6xl px-6", className)}
      {...props}
    />
  );
}

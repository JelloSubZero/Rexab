import type { InputHTMLAttributes, LabelHTMLAttributes } from "react";
import { clsx } from "@/lib/clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, id, className, ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <FieldLabel htmlFor={id}>{label}</FieldLabel>}
      <input
        id={id}
        className={clsx(
          "rounded-lg border bg-card px-3.5 py-2.5 text-sm text-primary placeholder:text-secondary",
          "focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent",
          "disabled:bg-bg disabled:text-secondary",
          error ? "border-negative" : "border-border",
          className,
        )}
        aria-invalid={Boolean(error)}
        {...props}
      />
      {error && <p className="text-xs text-negative">{error}</p>}
    </div>
  );
}

function FieldLabel(props: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className="text-sm font-medium text-primary"
      {...props}
    />
  );
}

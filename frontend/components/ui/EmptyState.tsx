import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({
  icon = "📭",
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-border py-12 text-center">
      <span className="text-3xl" aria-hidden="true">
        {icon}
      </span>
      <p className="font-medium text-primary">{title}</p>
      {description && (
        <p className="max-w-xs text-sm text-secondary">{description}</p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

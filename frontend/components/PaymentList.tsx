import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDateTime, formatMoney } from "@/lib/format";
import type { Payment } from "@/types/api";

interface PaymentListProps {
  payments: Payment[];
}

export function PaymentList({ payments }: PaymentListProps) {
  return (
    <Card>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-secondary">
        Payments
      </h2>

      {payments.length === 0 ? (
        <EmptyState
          icon="🧾"
          title="No payments yet"
          description="Add the first expense for this room."
        />
      ) : (
        <ul className="flex flex-col divide-y divide-border">
          {payments
            .slice()
            .reverse()
            .map((payment) => (
              <li key={payment.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="font-medium text-primary">
                    {payment.description || "Expense"}
                  </p>
                  <p className="text-sm text-secondary">
                    {payment.payer_name} paid ·{" "}
                    {formatDateTime(payment.created_at)}
                  </p>
                </div>
                <span className="font-semibold text-primary">
                  {formatMoney(payment.amount)}
                </span>
              </li>
            ))}
        </ul>
      )}
    </Card>
  );
}

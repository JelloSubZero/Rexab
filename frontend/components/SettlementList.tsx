"use client";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate, formatMoney } from "@/lib/format";
import { useTranslation } from "@/lib/i18n/LocaleProvider";
import type { Member, Settlement } from "@/types/api";

interface SettlementListProps {
  settlements: Settlement[];
  members: Member[];
  currentUserId: number;
  onConfirm: (settlement: Settlement) => void;
  isConfirming: number | null;
}

function nameFor(members: Member[], userId: number): string {
  return members.find((member) => member.user_id === userId)?.first_name ??
    "Someone";
}

export function SettlementList({
  settlements,
  members,
  currentUserId,
  onConfirm,
  isConfirming,
}: SettlementListProps) {
  const { t } = useTranslation();
  const pending = settlements.filter((s) => s.status === "pending");
  const history = settlements.filter((s) => s.status === "confirmed");

  return (
    <Card>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-secondary">
        {t("settlement.list.title")}
      </h2>

      {pending.length === 0 && history.length === 0 ? (
        <EmptyState icon="💸" title={t("settlement.list.emptyTitle")} />
      ) : (
        <div className="flex flex-col gap-4">
          {pending.length > 0 && (
            <div className="flex flex-col gap-2">
              {pending.map((settlement) => {
                const canConfirm = settlement.to_user_id === currentUserId;

                return (
                  <div
                    key={settlement.id}
                    className="rounded-lg border border-warning-bg bg-warning-bg p-3"
                  >
                    <p className="text-sm text-primary">
                      <span className="font-medium">
                        {nameFor(members, settlement.from_user_id)}
                      </span>{" "}
                      {t("settlement.list.owesWord")}{" "}
                      <span className="font-medium">
                        {nameFor(members, settlement.to_user_id)}
                      </span>
                    </p>
                    <p className="mt-1 text-lg font-semibold text-primary">
                      {formatMoney(settlement.amount)}
                    </p>
                    {canConfirm ? (
                      <Button
                        size="sm"
                        className="mt-2"
                        onClick={() => onConfirm(settlement)}
                        isLoading={isConfirming === settlement.id}
                      >
                        {t("room.actions.confirmPayment")}
                      </Button>
                    ) : (
                      <p className="mt-2 text-xs text-warning">
                        {t("settlement.list.waitingConfirmation")}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {history.length > 0 && (
            <ul className="flex flex-col divide-y divide-border">
              {history.map((settlement) => (
                <li key={settlement.id} className="py-2.5 text-sm">
                  <span className="text-positive">✓</span>{" "}
                  <span className="font-medium text-primary">
                    {nameFor(members, settlement.from_user_id)}
                  </span>{" "}
                  {t("common.paidWord")}{" "}
                  <span className="font-medium text-primary">
                    {nameFor(members, settlement.to_user_id)}
                  </span>{" "}
                  <span className="font-semibold">
                    {formatMoney(settlement.amount)}
                  </span>
                  {settlement.confirmed_at && (
                    <span className="text-secondary">
                      {" "}
                      · {formatDate(settlement.confirmed_at)}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </Card>
  );
}

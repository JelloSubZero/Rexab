"use client";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatMoney } from "@/lib/format";
import { useTranslation } from "@/lib/i18n/LocaleProvider";
import type { Member, Transfer } from "@/types/api";

interface WhoOwesWhomProps {
  transfers: Transfer[];
  members: Member[];
  currentUserId: number;
  onSettle: (transfer: Transfer) => void;
}

function nameFor(members: Member[], userId: number): string {
  return members.find((member) => member.user_id === userId)?.first_name ??
    "Someone";
}

export function WhoOwesWhom({
  transfers,
  members,
  currentUserId,
  onSettle,
}: WhoOwesWhomProps) {
  const { t } = useTranslation();

  return (
    <Card>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-secondary">
        {t("whoOwesWhom.title")}
      </h2>

      {transfers.length === 0 ? (
        <EmptyState icon="🎉" title={t("whoOwesWhom.emptyTitle")} />
      ) : (
        <ul className="flex flex-col divide-y divide-border">
          {transfers.map((transfer, index) => {
            const involvesCurrentUser =
              transfer.from_user_id === currentUserId ||
              transfer.to_user_id === currentUserId;

            return (
              <li
                key={index}
                className="flex items-center justify-between gap-3 py-3"
              >
                <p className="text-sm text-primary">
                  <span className="font-medium">
                    {nameFor(members, transfer.from_user_id)}
                  </span>{" "}
                  <span className="text-secondary">→</span>{" "}
                  <span className="font-medium">
                    {nameFor(members, transfer.to_user_id)}
                  </span>
                  <span className="ml-2 font-semibold">
                    {formatMoney(transfer.amount)}
                  </span>
                </p>
                {involvesCurrentUser && (
                  <Button size="sm" onClick={() => onSettle(transfer)}>
                    {t("room.actions.settleUp")}
                  </Button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}

"use client";

import { useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { api, getErrorMessage } from "@/lib/api";
import { useTranslation } from "@/lib/i18n/LocaleProvider";
import type { Member } from "@/types/api";

interface AddPaymentDialogProps {
  isOpen: boolean;
  onClose: () => void;
  roomId: number;
  members: Member[];
  currentUserId: number;
  onAdded: () => void;
}

export function AddPaymentDialog({
  isOpen,
  onClose,
  roomId,
  members,
  currentUserId,
  onAdded,
}: AddPaymentDialogProps) {
  const { t } = useTranslation();
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [payerId, setPayerId] = useState(currentUserId);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const parsedAmount = Number(amount.replace(",", "."));

    if (!Number.isFinite(parsedAmount) || parsedAmount <= 0) {
      setError(t("dialog.addPayment.invalidAmount"));
      return;
    }

    setIsSubmitting(true);

    try {
      await api.payments.create(roomId, {
        user_id: payerId,
        amount: parsedAmount,
        description: description.trim() || undefined,
      });
      setAmount("");
      setDescription("");
      onAdded();
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t("room.actions.addPayment")}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          id="amount"
          label={t("dialog.addPayment.amountLabel")}
          inputMode="decimal"
          placeholder={t("dialog.addPayment.amountPlaceholder")}
          required
          autoFocus
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
        />

        <Input
          id="description"
          label={t("dialog.addPayment.descriptionLabel")}
          placeholder={t("dialog.addPayment.descriptionPlaceholder")}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />

        <div className="flex flex-col gap-1.5">
          <label htmlFor="payer" className="text-sm font-medium text-primary">
            {t("dialog.addPayment.paidByLabel")}
          </label>
          <select
            id="payer"
            className="rounded-lg border border-border bg-card px-3.5 py-2.5 text-sm text-primary focus:outline-none focus:ring-2 focus:ring-accent"
            value={payerId}
            onChange={(event) => setPayerId(Number(event.target.value))}
          >
            {members.map((member) => (
              <option key={member.user_id} value={member.user_id}>
                {member.first_name}
                {member.user_id === currentUserId ? t("dialog.addPayment.youSuffix") : ""}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <p role="alert" className="text-sm text-negative">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            {t("room.actions.addPayment")}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

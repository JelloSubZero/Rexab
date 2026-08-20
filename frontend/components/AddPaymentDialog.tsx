"use client";

import { useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { api, getErrorMessage } from "@/lib/api";
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
      setError("Enter a valid amount.");
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
    <Modal isOpen={isOpen} onClose={onClose} title="Add payment">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          id="amount"
          label="Amount"
          inputMode="decimal"
          placeholder="100"
          required
          autoFocus
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
        />

        <Input
          id="description"
          label="Description"
          placeholder="Dinner"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />

        <div className="flex flex-col gap-1.5">
          <label htmlFor="payer" className="text-sm font-medium text-primary">
            Paid by
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
                {member.user_id === currentUserId ? " (you)" : ""}
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
            Cancel
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            Add payment
          </Button>
        </div>
      </form>
    </Modal>
  );
}

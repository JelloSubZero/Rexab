"use client";

import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel?: string;
  variant?: "primary" | "danger";
  isLoading?: boolean;
  error?: string | null;
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "Confirm",
  variant = "primary",
  isLoading = false,
  error,
}: ConfirmDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <p className="text-sm text-secondary">{description}</p>

      {error && (
        <p role="alert" className="mt-3 text-sm text-negative">
          {error}
        </p>
      )}

      <div className="mt-5 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button variant={variant} onClick={onConfirm} isLoading={isLoading}>
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}

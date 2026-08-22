"use client";

import { useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { api, getErrorMessage } from "@/lib/api";
import { useTranslation } from "@/lib/i18n/LocaleProvider";
import type { Room } from "@/types/api";

interface JoinRoomDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onJoined: (room: Room) => void;
}

export function JoinRoomDialog({
  isOpen,
  onClose,
  onJoined,
}: JoinRoomDialogProps) {
  const { t } = useTranslation();
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const room = await api.rooms.join(code.trim().toUpperCase());
      setCode("");
      onJoined(room);
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t("dialog.joinRoom.title")}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          id="invite-code"
          label={t("dialog.joinRoom.codeLabel")}
          placeholder="X7K4-P9Q2"
          required
          autoFocus
          value={code}
          onChange={(event) => setCode(event.target.value)}
        />

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
            {t("room.actions.join")}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

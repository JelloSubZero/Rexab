"use client";

import { useState, type FormEvent } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { api, getErrorMessage } from "@/lib/api";
import type { Room } from "@/types/api";

interface CreateRoomDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (room: Room) => void;
}

export function CreateRoomDialog({
  isOpen,
  onClose,
  onCreated,
}: CreateRoomDialogProps) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const room = await api.rooms.create(name.trim());
      setName("");
      onCreated(room);
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create room">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          id="room-name"
          label="Room name"
          placeholder="Apartment"
          required
          autoFocus
          value={name}
          onChange={(event) => setName(event.target.value)}
        />

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
            Create room
          </Button>
        </div>
      </form>
    </Modal>
  );
}

"use client";

import { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { useTranslation } from "@/lib/i18n/LocaleProvider";

interface InviteDialogProps {
  isOpen: boolean;
  onClose: () => void;
  code: string;
}

export function InviteDialog({ isOpen, onClose, code }: InviteDialogProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t("dialog.invite.title")}>
      <p className="text-sm text-secondary">
        {t("dialog.invite.description")}
      </p>
      <p className="mt-4 rounded-lg border border-border bg-bg px-4 py-3 text-center text-xl font-semibold tracking-widest text-primary">
        {code}
      </p>
      <div className="mt-4 flex justify-end">
        <Button onClick={handleCopy}>
          {copied ? t("room.actions.copied") : t("room.actions.copyCode")}
        </Button>
      </div>
    </Modal>
  );
}

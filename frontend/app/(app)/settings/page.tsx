"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useTranslation } from "@/lib/i18n/LocaleProvider";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const router = useRouter();

  if (!user) return null;

  return (
    <div className="mx-auto flex max-w-md flex-col gap-6">
      <h1 className="text-2xl font-semibold text-primary">{t("nav.settings")}</h1>

      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/10 text-lg font-semibold text-accent">
            {user.first_name.charAt(0).toUpperCase()}
          </span>
          <div>
            <p className="font-medium text-primary">{user.first_name}</p>
            <p className="text-sm text-secondary">
              {user.email ?? t("settings.noEmail")}
            </p>
          </div>
        </div>

        {user.telegram_id && (
          <p className="text-sm text-secondary">
            {t("settings.linkedTelegram", { id: user.telegram_id })}
          </p>
        )}
      </Card>

      <Button
        variant="secondary"
        onClick={() => {
          logout();
          router.replace("/login");
        }}
      >
        {t("nav.logout")}
      </Button>
    </div>
  );
}

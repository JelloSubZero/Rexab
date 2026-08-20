"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRoomData } from "@/hooks/useRoomData";
import { api, getErrorMessage } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { StatTile } from "@/components/ui/StatTile";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { MemberList } from "@/components/MemberList";
import { PaymentList } from "@/components/PaymentList";
import { SettlementList } from "@/components/SettlementList";
import { WhoOwesWhom } from "@/components/WhoOwesWhom";
import { AddPaymentDialog } from "@/components/AddPaymentDialog";
import { InviteDialog } from "@/components/InviteDialog";
import { formatMoney, formatSignedMoney } from "@/lib/format";
import type { Member, Settlement, Transfer } from "@/types/api";

export default function RoomPage() {
  const params = useParams<{ id: string }>();
  const roomId = Number(params.id);
  const router = useRouter();
  const { user } = useAuth();
  const { showToast } = useToast();
  const { data, error, reload } = useRoomData(roomId);

  const [isAddPaymentOpen, setIsAddPaymentOpen] = useState(false);
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [settleTarget, setSettleTarget] = useState<Transfer | null>(null);
  const [confirmTarget, setConfirmTarget] = useState<Settlement | null>(null);
  const [removeTarget, setRemoveTarget] = useState<Member | null>(null);
  const [leaveOrDelete, setLeaveOrDelete] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isActing, setIsActing] = useState(false);

  if (error) {
    return (
      <div className="mx-auto max-w-2xl">
        <p className="text-sm text-negative">{error}</p>
      </div>
    );
  }

  if (!data || !user) {
    return (
      <div className="mx-auto flex max-w-4xl flex-col gap-4">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-40" />
      </div>
    );
  }

  const { room, members, payments, settlements, dashboard } = data;

  async function handleSettle() {
    if (!settleTarget) return;
    setIsActing(true);
    setActionError(null);

    try {
      await api.settlements.create(roomId, {
        from_user_id: settleTarget.from_user_id,
        to_user_id: settleTarget.to_user_id,
        amount: settleTarget.amount,
      });
      showToast("Settlement requested.");
      setSettleTarget(null);
      await reload();
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setIsActing(false);
    }
  }

  async function handleConfirmSettlement() {
    if (!confirmTarget) return;
    setIsActing(true);
    setActionError(null);

    try {
      await api.settlements.confirm(confirmTarget.id);
      showToast("Payment confirmed.");
      setConfirmTarget(null);
      await reload();
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setIsActing(false);
    }
  }

  async function handleRemoveMember() {
    if (!removeTarget) return;
    setIsActing(true);
    setActionError(null);

    try {
      await api.members.remove(roomId, removeTarget.user_id);
      showToast(`${removeTarget.first_name} removed from the room.`);
      setRemoveTarget(null);
      await reload();
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setIsActing(false);
    }
  }

  async function handleLeaveOrDelete() {
    setIsActing(true);
    setActionError(null);

    try {
      if (room.is_owner) {
        await api.rooms.delete(roomId);
        showToast("Room deleted.");
      } else {
        await api.rooms.leave(roomId);
        showToast("You left the room.");
      }
      router.replace("/dashboard");
    } catch (err) {
      setActionError(getErrorMessage(err));
      setIsActing(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-primary">
            {room.name ?? `Room ${room.code}`}
          </h1>
          <p className="mt-1 text-sm text-secondary">
            {members.length} {members.length === 1 ? "member" : "members"} ·
            code <span className="font-mono">{room.code}</span>
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setLeaveOrDelete(true)}
        >
          {room.is_owner ? "Delete room" : "Leave room"}
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile
          label="You owe"
          value={formatSignedMoney(-dashboard.you_owe)}
          tone={dashboard.you_owe > 0 ? "negative" : "neutral"}
        />
        <StatTile
          label="Owed to you"
          value={formatSignedMoney(dashboard.you_are_owed)}
          tone={dashboard.you_are_owed > 0 ? "positive" : "neutral"}
        />
        <StatTile
          label="Balance"
          value={formatSignedMoney(dashboard.balance)}
          tone={
            dashboard.balance > 0
              ? "positive"
              : dashboard.balance < 0
                ? "negative"
                : "neutral"
          }
        />
      </div>

      <WhoOwesWhom
        transfers={dashboard.transfers}
        members={members}
        currentUserId={user.id}
        onSettle={setSettleTarget}
      />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-[1fr_260px]">
        <div className="flex flex-col gap-6 md:order-1">
          <div>
            <div className="mb-3 flex items-center justify-between">
              <span />
              <Button size="sm" onClick={() => setIsAddPaymentOpen(true)}>
                + Add payment
              </Button>
            </div>
            <PaymentList payments={payments} />
          </div>

          <SettlementList
            settlements={settlements}
            members={members}
            currentUserId={user.id}
            onConfirm={setConfirmTarget}
            isConfirming={isActing ? (confirmTarget?.id ?? null) : null}
          />
        </div>

        <div className="md:order-2">
          <MemberList
            members={members}
            isOwner={room.is_owner}
            onInvite={() => setIsInviteOpen(true)}
            onRemove={setRemoveTarget}
          />
        </div>
      </div>

      <AddPaymentDialog
        isOpen={isAddPaymentOpen}
        onClose={() => setIsAddPaymentOpen(false)}
        roomId={roomId}
        members={members}
        currentUserId={user.id}
        onAdded={() => {
          showToast("Payment added.");
          reload();
        }}
      />

      <InviteDialog
        isOpen={isInviteOpen}
        onClose={() => setIsInviteOpen(false)}
        code={room.code}
      />

      <ConfirmDialog
        isOpen={settleTarget !== null}
        onClose={() => {
          setSettleTarget(null);
          setActionError(null);
        }}
        onConfirm={handleSettle}
        title="Request settlement?"
        description={
          settleTarget
            ? `Mark ${formatMoney(settleTarget.amount)} as being settled between these two members. The receiver will need to confirm.`
            : ""
        }
        confirmLabel="Request settlement"
        isLoading={isActing}
        error={actionError}
      />

      <ConfirmDialog
        isOpen={confirmTarget !== null}
        onClose={() => {
          setConfirmTarget(null);
          setActionError(null);
        }}
        onConfirm={handleConfirmSettlement}
        title="Confirm payment?"
        description="Did you actually receive this payment? Confirming will mark the debt as settled."
        confirmLabel="Confirm"
        isLoading={isActing}
        error={actionError}
      />

      <ConfirmDialog
        isOpen={removeTarget !== null}
        onClose={() => {
          setRemoveTarget(null);
          setActionError(null);
        }}
        onConfirm={handleRemoveMember}
        title="Remove member?"
        description={
          removeTarget
            ? `${removeTarget.first_name} will lose access to this room.`
            : ""
        }
        confirmLabel="Remove"
        variant="danger"
        isLoading={isActing}
        error={actionError}
      />

      <ConfirmDialog
        isOpen={leaveOrDelete}
        onClose={() => {
          setLeaveOrDelete(false);
          setActionError(null);
        }}
        onConfirm={handleLeaveOrDelete}
        title={room.is_owner ? "Delete this room?" : "Leave this room?"}
        description={
          room.is_owner
            ? "This permanently deletes the room and all its payments, receipts and settlements. This cannot be undone."
            : "You can rejoin later with the invite code."
        }
        confirmLabel={room.is_owner ? "Delete room" : "Leave room"}
        variant="danger"
        isLoading={isActing}
        error={actionError}
      />
    </div>
  );
}

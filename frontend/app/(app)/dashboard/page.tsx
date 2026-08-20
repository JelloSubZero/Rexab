"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, getErrorMessage } from "@/lib/api";
import { StatTile } from "@/components/ui/StatTile";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { RoomCard } from "@/components/RoomCard";
import { CreateRoomDialog } from "@/components/CreateRoomDialog";
import { JoinRoomDialog } from "@/components/JoinRoomDialog";
import { formatSignedMoney } from "@/lib/format";
import { aggregateDashboardTotals } from "@/lib/dashboard-totals";
import type { Room } from "@/types/api";

interface RoomWithBalance {
  room: Room;
  balance: number | null;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [rooms, setRooms] = useState<RoomWithBalance[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isJoinOpen, setIsJoinOpen] = useState(false);

  const loadRooms = useCallback(async () => {
    setError(null);

    try {
      const roomList = await api.rooms.list();

      const withBalances = await Promise.all(
        roomList.map(async (room) => {
          try {
            const dashboard = await api.rooms.dashboard(room.id);
            return { room, balance: dashboard.balance };
          } catch {
            return { room, balance: null };
          }
        }),
      );

      setRooms(withBalances);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadRooms();
  }, [loadRooms]);

  const { youOwe, youAreOwed, netBalance } = aggregateDashboardTotals(
    rooms ?? [],
  );

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold text-primary">
          Good to see you, {user?.first_name}
        </h1>
        <p className="mt-1 text-sm text-secondary">
          Here&apos;s what&apos;s happening in your rooms.
        </p>
      </div>

      {rooms === null && !error ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatTile
            label="You owe"
            value={formatSignedMoney(-youOwe)}
            tone={youOwe > 0 ? "negative" : "neutral"}
          />
          <StatTile
            label="Owed to you"
            value={formatSignedMoney(youAreOwed)}
            tone={youAreOwed > 0 ? "positive" : "neutral"}
          />
          <StatTile
            label="Balance"
            value={formatSignedMoney(netBalance)}
            tone={
              netBalance > 0
                ? "positive"
                : netBalance < 0
                  ? "negative"
                  : "neutral"
            }
          />
        </div>
      )}

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-primary">Your rooms</h2>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsJoinOpen(true)}
            >
              Join room
            </Button>
            <Button size="sm" onClick={() => setIsCreateOpen(true)}>
              + Create room
            </Button>
          </div>
        </div>

        {error && (
          <p role="alert" className="text-sm text-negative">
            {error}
          </p>
        )}

        {rooms === null && !error && (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
        )}

        {rooms !== null && rooms.length === 0 && (
          <EmptyState
            icon="🏠"
            title="No rooms yet"
            description="Create a room to start splitting expenses, or join one with an invite code."
            action={
              <Button size="sm" onClick={() => setIsCreateOpen(true)}>
                + Create room
              </Button>
            }
          />
        )}

        {rooms !== null && rooms.length > 0 && (
          <div className="flex flex-col gap-3">
            {rooms.map(({ room, balance }) => (
              <RoomCard key={room.id} room={room} balance={balance} />
            ))}
          </div>
        )}
      </div>

      <CreateRoomDialog
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreated={() => loadRooms()}
      />
      <JoinRoomDialog
        isOpen={isJoinOpen}
        onClose={() => setIsJoinOpen(false)}
        onJoined={() => loadRooms()}
      />
    </div>
  );
}

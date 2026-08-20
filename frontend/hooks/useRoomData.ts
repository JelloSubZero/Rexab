"use client";

import { useCallback, useEffect, useState } from "react";
import { api, getErrorMessage } from "@/lib/api";
import type { Dashboard, Member, Payment, Room, Settlement } from "@/types/api";

interface RoomData {
  room: Room;
  members: Member[];
  payments: Payment[];
  settlements: Settlement[];
  dashboard: Dashboard;
}

export function useRoomData(roomId: number) {
  const [data, setData] = useState<RoomData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const [room, members, payments, settlements, dashboard] =
        await Promise.all([
          api.rooms.get(roomId),
          api.members.list(roomId),
          api.payments.list(roomId),
          api.settlements.list(roomId),
          api.rooms.dashboard(roomId),
        ]);

      setData({ room, members, payments, settlements, dashboard });
      setError(null);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, [roomId]);

  useEffect(() => {
    // Fetching room data on mount/roomId change is the standard
    // "synchronize with an external system" use of an effect; the
    // resulting setState only happens after the fetch resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    reload();
  }, [reload]);

  return { data, error, reload };
}

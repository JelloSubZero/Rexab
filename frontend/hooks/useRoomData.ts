"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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
  // Tracks the room currently being displayed so a slow fetch for a room
  // the user has since navigated away from can't overwrite newer data.
  const roomIdRef = useRef(roomId);
  useEffect(() => {
    roomIdRef.current = roomId;
  });

  const reload = useCallback(async () => {
    const requestedRoomId = roomId;

    try {
      const [room, members, payments, settlements, dashboard] =
        await Promise.all([
          api.rooms.get(roomId),
          api.members.list(roomId),
          api.payments.list(roomId),
          api.settlements.list(roomId),
          api.rooms.dashboard(roomId),
        ]);

      if (roomIdRef.current !== requestedRoomId) return;

      setData({ room, members, payments, settlements, dashboard });
      setError(null);
    } catch (err) {
      if (roomIdRef.current !== requestedRoomId) return;
      setError(getErrorMessage(err));
    }
  }, [roomId]);

  useEffect(() => {
    // Clear the previous room's data immediately so it can't be shown
    // under the new room while the new fetch is in flight.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setData(null);
    reload();
  }, [reload]);

  return { data, error, reload };
}

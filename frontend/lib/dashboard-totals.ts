export interface RoomBalance {
  balance: number | null;
}

export interface DashboardTotals {
  youOwe: number;
  youAreOwed: number;
  netBalance: number;
}

/**
 * Sums each room's own server-computed balance into cross-room
 * totals. Rooms whose balance failed to load (null) are excluded
 * rather than treated as zero, so a fetch failure doesn't silently
 * understate what the user owes.
 */
export function aggregateDashboardTotals(
  rooms: RoomBalance[],
): DashboardTotals {
  const totals = rooms.reduce(
    (acc, { balance }) => {
      if (balance === null) return acc;
      if (balance > 0) acc.youAreOwed += balance;
      if (balance < 0) acc.youOwe += -balance;
      return acc;
    },
    { youOwe: 0, youAreOwed: 0 },
  );

  return {
    ...totals,
    netBalance: totals.youAreOwed - totals.youOwe,
  };
}

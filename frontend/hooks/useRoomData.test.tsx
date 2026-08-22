import { act, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { useRoomData } from "@/hooks/useRoomData";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  api: {
    rooms: { get: vi.fn(), dashboard: vi.fn() },
    members: { list: vi.fn() },
    payments: { list: vi.fn() },
    settlements: { list: vi.fn() },
  },
  getErrorMessage: (e: unknown) => (e instanceof Error ? e.message : "error"),
}));

function makeRoom(id: number) {
  return { id, name: `Room ${id}`, code: `CODE${id}`, is_owner: true };
}

function TestConsumer({ roomId }: { roomId: number }) {
  const { data } = useRoomData(roomId);
  if (!data) return <p>loading</p>;
  return <p>room name: {data.room.name}</p>;
}

describe("useRoomData", () => {
  beforeEach(() => {
    vi.mocked(api.members.list).mockResolvedValue([]);
    vi.mocked(api.payments.list).mockResolvedValue([]);
    vi.mocked(api.settlements.list).mockResolvedValue([]);
    vi.mocked(api.rooms.dashboard).mockResolvedValue({
      you_owe: 0,
      you_are_owed: 0,
      balance: 0,
      transfers: [],
    });
  });

  it("does not show a previous room's data after switching rooms, even if that room's fetch resolves later", async () => {
    let resolveRoom1: (value: unknown) => void;
    const room1Promise = new Promise((resolve) => {
      resolveRoom1 = resolve;
    });

    vi.mocked(api.rooms.get).mockImplementation((id: number) => {
      if (id === 1) return room1Promise as Promise<never>;
      return Promise.resolve(makeRoom(id));
    });

    const { rerender } = render(<TestConsumer roomId={1} />);

    await waitFor(() => expect(api.rooms.get).toHaveBeenCalledWith(1));

    // Navigate to room 2 before room 1's fetch resolves.
    rerender(<TestConsumer roomId={2} />);

    await waitFor(() =>
      expect(screen.getByText("room name: Room 2")).toBeInTheDocument(),
    );

    // Room 1's slow fetch finally resolves after we've already switched away.
    await act(async () => {
      resolveRoom1(makeRoom(1));
    });

    expect(screen.getByText("room name: Room 2")).toBeInTheDocument();
  });
});

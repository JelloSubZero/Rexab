import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { WhoOwesWhom } from "@/components/WhoOwesWhom";
import type { Member, Transfer } from "@/types/api";

const members: Member[] = [
  {
    user_id: 1,
    first_name: "Daniel",
    username: null,
    is_owner: true,
    joined_at: "2026-01-01T00:00:00Z",
  },
  {
    user_id: 2,
    first_name: "Alex",
    username: null,
    is_owner: false,
    joined_at: "2026-01-01T00:00:00Z",
  },
  {
    user_id: 3,
    first_name: "John",
    username: null,
    is_owner: false,
    joined_at: "2026-01-01T00:00:00Z",
  },
];

describe("WhoOwesWhom", () => {
  it("shows an empty state when there are no transfers", () => {
    render(
      <WhoOwesWhom
        transfers={[]}
        members={members}
        currentUserId={1}
        onSettle={vi.fn()}
      />,
    );

    expect(screen.getByText(/settled up/i)).toBeInTheDocument();
  });

  it("shows a Settle up button only for transfers involving the current user", () => {
    const transfers: Transfer[] = [
      { from_user_id: 2, to_user_id: 1, amount: 50 }, // involves user 1
      { from_user_id: 3, to_user_id: 2, amount: 20 }, // does not
    ];

    render(
      <WhoOwesWhom
        transfers={transfers}
        members={members}
        currentUserId={1}
        onSettle={vi.fn()}
      />,
    );

    expect(screen.getAllByText("Settle up")).toHaveLength(1);
  });

  it("resolves user ids to first names", () => {
    render(
      <WhoOwesWhom
        transfers={[{ from_user_id: 2, to_user_id: 1, amount: 50 }]}
        members={members}
        currentUserId={1}
        onSettle={vi.fn()}
      />,
    );

    expect(screen.getByText("Alex")).toBeInTheDocument();
    expect(screen.getByText("Daniel")).toBeInTheDocument();
    expect(screen.getByText("50.00 zł")).toBeInTheDocument();
  });

  it("calls onSettle with the clicked transfer", async () => {
    const onSettle = vi.fn();
    const transfer: Transfer = { from_user_id: 2, to_user_id: 1, amount: 50 };
    const user = userEvent.setup();

    render(
      <WhoOwesWhom
        transfers={[transfer]}
        members={members}
        currentUserId={1}
        onSettle={onSettle}
      />,
    );

    await user.click(screen.getByText("Settle up"));

    expect(onSettle).toHaveBeenCalledWith(transfer);
  });
});

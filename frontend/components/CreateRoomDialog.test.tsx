import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { CreateRoomDialog } from "@/components/CreateRoomDialog";
import { api, ApiError } from "@/lib/api";
import type { Room } from "@/types/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>(
    "@/lib/api",
  );
  return {
    ...actual,
    api: { rooms: { create: vi.fn() } },
  };
});

const mockRoom: Room = {
  id: 1,
  code: "ABCD1234",
  name: "Apartment",
  status: "active",
  owner_id: 1,
  is_owner: true,
  members_count: 1,
  created_at: "2026-01-01T00:00:00Z",
};

describe("CreateRoomDialog", () => {
  it("submits the entered name and reports the created room", async () => {
    vi.mocked(api.rooms.create).mockResolvedValue(mockRoom);
    const onCreated = vi.fn();
    const onClose = vi.fn();
    const user = userEvent.setup();

    render(
      <CreateRoomDialog isOpen onClose={onClose} onCreated={onCreated} />,
    );

    await user.type(screen.getByLabelText("Room name"), "Apartment");
    await user.click(screen.getByRole("button", { name: "Create room" }));

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(mockRoom));
    expect(api.rooms.create).toHaveBeenCalledWith("Apartment");
    expect(onClose).toHaveBeenCalled();
  });

  it("shows the API error message and keeps the dialog open on failure", async () => {
    vi.mocked(api.rooms.create).mockRejectedValue(
      new ApiError(400, "BAD_REQUEST", "Name is required."),
    );
    const onCreated = vi.fn();
    const onClose = vi.fn();
    const user = userEvent.setup();

    render(
      <CreateRoomDialog isOpen onClose={onClose} onCreated={onCreated} />,
    );

    await user.type(screen.getByLabelText("Room name"), "x");
    await user.click(screen.getByRole("button", { name: "Create room" }));

    await waitFor(() =>
      expect(screen.getByText("Name is required.")).toBeInTheDocument(),
    );
    expect(onCreated).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("does not render when closed", () => {
    render(
      <CreateRoomDialog
        isOpen={false}
        onClose={vi.fn()}
        onCreated={vi.fn()}
      />,
    );

    expect(screen.queryByLabelText("Room name")).not.toBeInTheDocument();
  });
});

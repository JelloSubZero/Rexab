import Link from "next/link";
import { formatSignedMoney } from "@/lib/format";
import { clsx } from "@/lib/clsx";
import type { Room } from "@/types/api";

interface RoomCardProps {
  room: Room;
  balance: number | null;
}

export function RoomCard({ room, balance }: RoomCardProps) {
  const tone =
    balance === null
      ? "text-secondary"
      : balance > 0
        ? "text-positive"
        : balance < 0
          ? "text-negative"
          : "text-secondary";

  return (
    <Link
      href={`/rooms/${room.id}`}
      className="flex items-center justify-between rounded-xl border border-border bg-card p-4 shadow-sm transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      <div>
        <p className="font-medium text-primary">
          {room.name ?? `Room ${room.code}`}
        </p>
        <p className="text-sm text-secondary">
          {room.members_count}{" "}
          {room.members_count === 1 ? "member" : "members"}
        </p>
      </div>
      <span className={clsx("font-semibold", tone)}>
        {balance === null ? "—" : formatSignedMoney(balance)}
      </span>
    </Link>
  );
}

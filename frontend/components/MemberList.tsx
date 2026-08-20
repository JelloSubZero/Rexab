import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import type { Member } from "@/types/api";

interface MemberListProps {
  members: Member[];
  isOwner: boolean;
  onInvite: () => void;
  onRemove: (member: Member) => void;
}

export function MemberList({
  members,
  isOwner,
  onInvite,
  onRemove,
}: MemberListProps) {
  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-secondary">
          Members
        </h2>
        <span className="text-sm text-secondary">{members.length}</span>
      </div>
      <ul className="flex flex-col divide-y divide-border">
        {members.map((member) => (
          <li
            key={member.user_id}
            className="flex items-center gap-2 py-2.5 text-sm"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/10 text-xs font-semibold text-accent">
              {member.first_name.charAt(0).toUpperCase()}
            </span>
            <span className="flex-1 text-primary">{member.first_name}</span>
            {member.is_owner && <span aria-label="Owner">👑</span>}
            {isOwner && !member.is_owner && (
              <button
                onClick={() => onRemove(member)}
                className="text-xs font-medium text-negative hover:underline"
              >
                Remove
              </button>
            )}
          </li>
        ))}
      </ul>
      <Button
        variant="secondary"
        size="sm"
        className="mt-3 w-full"
        onClick={onInvite}
      >
        + Add member
      </Button>
    </Card>
  );
}

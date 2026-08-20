from datetime import datetime

from pydantic import BaseModel

from database.models import RoomMember


class MemberResponse(BaseModel):
    user_id: int
    first_name: str
    username: str | None
    is_owner: bool
    joined_at: datetime

    @classmethod
    def from_member(
        cls,
        member: RoomMember,
        owner_id: int,
    ) -> "MemberResponse":
        return cls(
            user_id=member.user_id,
            first_name=(
                member.user.first_name if member.user else ""
            ),
            username=member.user.username if member.user else None,
            is_owner=member.user_id == owner_id,
            joined_at=member.joined_at,
        )

from datetime import datetime

from pydantic import BaseModel, Field

from database.models import Room


class RoomResponse(BaseModel):
    id: int
    code: str
    name: str | None
    status: str
    owner_id: int
    is_owner: bool
    members_count: int
    created_at: datetime

    @classmethod
    def from_room(
        cls,
        room: Room,
        is_owner: bool,
        members_count: int,
    ) -> "RoomResponse":
        return cls(
            id=room.id,
            code=room.code,
            name=room.name,
            status=room.status,
            owner_id=room.owner_id,
            is_owner=is_owner,
            members_count=members_count,
            created_at=room.created_at,
        )


class RoomCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class RoomJoinRequest(BaseModel):
    code: str = Field(min_length=1, max_length=8)

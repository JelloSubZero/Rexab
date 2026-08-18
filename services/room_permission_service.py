from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from services.room_service import RoomService


class RemoveMemberPermission(StrEnum):
    ALLOWED = "allowed"
    ROOM_NOT_FOUND = "room_not_found"
    NOT_OWNER = "not_owner"
    OWNER_CANNOT_BE_REMOVED = "owner_cannot_be_removed"


class RoomPermissionService:

    @staticmethod
    async def is_owner(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ) -> bool:
        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        if room is None:
            return False

        return room.owner_id == user_id

    @staticmethod
    async def can_remove_member(
        session: AsyncSession,
        room_id: int,
        actor_user_id: int,
        target_user_id: int,
    ) -> RemoveMemberPermission:
        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        if room is None:
            return RemoveMemberPermission.ROOM_NOT_FOUND

        if room.owner_id != actor_user_id:
            return RemoveMemberPermission.NOT_OWNER

        if target_user_id == room.owner_id:
            return RemoveMemberPermission.OWNER_CANNOT_BE_REMOVED

        return RemoveMemberPermission.ALLOWED
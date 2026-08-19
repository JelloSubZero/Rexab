from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from services.room_access_service import RoomAccessService


class ReceiptPermission(StrEnum):
    ALLOWED = "allowed"
    NOT_MEMBER = "not_member"


class ReceiptPermissionService:

    @staticmethod
    async def can_manage(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ) -> ReceiptPermission:

        has_access = await RoomAccessService.check_access(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

        if not has_access:
            return ReceiptPermission.NOT_MEMBER

        return ReceiptPermission.ALLOWED
from sqlalchemy.ext.asyncio import AsyncSession

from services.room_member_service import RoomMemberService


class RoomAccessService:

    @staticmethod
    async def check_access(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ) -> bool:

        return await RoomMemberService.is_member(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )
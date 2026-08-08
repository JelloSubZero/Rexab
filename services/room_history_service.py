from sqlalchemy.ext.asyncio import AsyncSession

from repositories.room_history_repository import (
    RoomHistoryRepository,
)


class RoomHistoryService:

    @staticmethod
    async def create(
        session: AsyncSession,
        room_id: int,
        user_id: int,
        action: str,
        description: str | None = None,
        amount: float | None = None,
    ):
        return await RoomHistoryRepository.create(
            session=session,
            room_id=room_id,
            user_id=user_id,
            action=action,
            description=description,
            amount=amount,
        )

    @staticmethod
    async def get_room_history(
        session: AsyncSession,
        room_id: int,
    ):
        return await RoomHistoryRepository.get_by_room(
            session=session,
            room_id=room_id,
        )
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.room_view_repository import RoomViewRepository


class RoomViewStoreService:

    @staticmethod
    async def save(
        session: AsyncSession,
        room_id: int,
        user_id: int,
        message_id: int,
    ):
        return await RoomViewRepository.save(
            session=session,
            room_id=room_id,
            user_id=user_id,
            message_id=message_id,
        )

    @staticmethod
    async def get(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):
        return await RoomViewRepository.get(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

    @staticmethod
    async def get_all(
        session: AsyncSession,
        room_id: int,
    ):
        return await RoomViewRepository.get_all(
            session=session,
            room_id=room_id,
        )
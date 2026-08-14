from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import RoomMessage


class RoomMessageRepository:

    @staticmethod
    async def create(
        session: AsyncSession,
        room_id: int,
        chat_id: int,
        message_id: int,
    ):
        message = RoomMessage(
            room_id=room_id,
            chat_id=chat_id,
            message_id=message_id,
        )

        session.add(message)

        await session.flush()

        return message

    @staticmethod
    async def get_by_room(
        session: AsyncSession,
        room_id: int,
    ):
        result = await session.execute(
            select(RoomMessage).where(
                RoomMessage.room_id == room_id
            )
        )

        return result.scalars().all()

    @staticmethod
    async def delete_by_room(
        session: AsyncSession,
        room_id: int,
    ):
        await session.execute(
            delete(RoomMessage).where(
                RoomMessage.room_id == room_id
            )
        )
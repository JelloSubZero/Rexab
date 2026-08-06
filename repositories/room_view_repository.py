from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import RoomView


class RoomViewRepository:

    @staticmethod
    async def save(
        session: AsyncSession,
        room_id: int,
        user_id: int,
        chat_id: int,
        message_id: int,
    ):

        view = await RoomViewRepository.get(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

        if view:

            view.chat_id = chat_id
            view.message_id = message_id

            await session.commit()

            return view

        view = RoomView(
            room_id=room_id,
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
        )

        session.add(view)

        await session.commit()
        await session.refresh(view)

        print("===== ROOM VIEW =====")
        print(f"room={room_id}")
        print(f"user={user_id}")
        print(f"chat={chat_id}")
        print(f"message={message_id}")
        print("=====================")

        return view

    @staticmethod
    async def get(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):

        result = await session.execute(
            select(RoomView).where(
                RoomView.room_id == room_id,
                RoomView.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        session: AsyncSession,
        room_id: int,
    ):

        result = await session.execute(
            select(RoomView).where(
                RoomView.room_id == room_id,
            )
        )

        return list(result.scalars().all())
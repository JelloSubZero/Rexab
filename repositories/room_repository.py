from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Room,
    Receipt,
    RoomMember,
    RoomView,
    RoomPayment,
    RoomHistory,
    RoomSettlement,
)


class RoomRepository:

    @staticmethod
    async def get_by_code(
        session: AsyncSession,
        code: str,
    ) -> Room | None:

        result = await session.execute(
            select(Room).where(Room.code == code)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        owner_id: int,
        code: str,
    ) -> Room:

        room = Room(
            owner_id=owner_id,
            code=code,
        )

        session.add(room)

        await session.commit()
        await session.refresh(room)

        return room

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        room_id: int,
    ) -> Room | None:

        return await session.get(
            Room,
            room_id,
        )

    @staticmethod
    async def delete(
        session: AsyncSession,
        room_id: int,
    ) -> bool:

        room = await session.get(
            Room,
            room_id,
        )

        if room is None:
            return False

        # --------------------------------
        # УДАЛЯЕМ ВСЕ ДАННЫЕ КОМНАТЫ
        # --------------------------------

        await session.execute(
            delete(RoomView).where(
                RoomView.room_id == room_id
            )
        )

        await session.execute(
            delete(RoomSettlement).where(
                RoomSettlement.room_id == room_id
            )
        )

        await session.execute(
            delete(RoomPayment).where(
                RoomPayment.room_id == room_id
            )
        )

        await session.execute(
            delete(RoomHistory).where(
                RoomHistory.room_id == room_id
            )
        )

        await session.execute(
            delete(Receipt).where(
                Receipt.room_id == room_id
            )
        )

        await session.execute(
            delete(RoomMember).where(
                RoomMember.room_id == room_id
            )
        )

        # --------------------------------
        # УДАЛЯЕМ САМУ КОМНАТУ
        # --------------------------------

        await session.delete(room)

        await session.commit()

        return True
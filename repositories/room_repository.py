from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Room


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
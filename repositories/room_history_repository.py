from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import RoomHistory


class RoomHistoryRepository:

    @staticmethod
    async def create(
        session: AsyncSession,
        room_id: int,
        user_id: int,
        action: str,
        description: str | None = None,
        amount: float | None = None,
    ) -> RoomHistory:

        history = RoomHistory(
            room_id=room_id,
            user_id=user_id,
            action=action,
            description=description,
            amount=amount,
        )

        session.add(history)

        await session.commit()
        await session.refresh(history)

        return history

    @staticmethod
    async def get_by_room(
        session: AsyncSession,
        room_id: int,
    ) -> list[RoomHistory]:

        result = await session.execute(
            select(RoomHistory)
            .options(
                selectinload(RoomHistory.user)
            )
            .where(
                RoomHistory.room_id == room_id
            )
            .order_by(
                RoomHistory.created_at.desc()
            )
        )

        return list(result.scalars().all())
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Room, RoomMember
from sqlalchemy.orm import selectinload


class RoomMemberRepository:

    @staticmethod
    async def add_member(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ) -> RoomMember:

        member = RoomMember(
            room_id=room_id,
            user_id=user_id,
        )

        session.add(member)

        await session.flush()

        return member

    @staticmethod
    async def is_member(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ) -> bool:

        result = await session.execute(
            select(RoomMember).where(
                RoomMember.room_id == room_id,
                RoomMember.user_id == user_id,
            )
        )

        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_members(
        session: AsyncSession,
        room_id: int,
    ) -> list[RoomMember]:

        result = await session.execute(
            select(RoomMember)
            .options(
                selectinload(RoomMember.user),
            )
            .where(
                RoomMember.room_id == room_id,
            )
        )

        return list(result.scalars().all())

    @staticmethod
    async def get_rooms_for_user(
        session: AsyncSession,
        user_id: int,
    ) -> list[Room]:

        result = await session.execute(
            select(Room)
            .join(
                RoomMember,
                RoomMember.room_id == Room.id,
            )
            .where(
                RoomMember.user_id == user_id,
            )
            .order_by(Room.created_at.desc())
        )

        return list(result.scalars().all())

    @staticmethod
    async def remove_member(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ) -> bool:

        result = await session.execute(
            select(RoomMember).where(
                RoomMember.room_id == room_id,
                RoomMember.user_id == user_id,
            )
        )

        member = result.scalar_one_or_none()

        if member is None:
            return False

        await session.delete(member)
        await session.flush()

        return True
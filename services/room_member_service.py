from sqlalchemy.ext.asyncio import AsyncSession

from repositories.room_member_repository import RoomMemberRepository


class RoomMemberService:

    @staticmethod
    async def join_room(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):
        """
        Добавляет пользователя в комнату,
        если его там еще нет.
        """

        exists = await RoomMemberRepository.is_member(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

        if exists:
            return None

        return await RoomMemberRepository.add_member(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

    @staticmethod
    async def get_members(
        session: AsyncSession,
        room_id: int,
    ):
        return await RoomMemberRepository.get_members(
            session=session,
            room_id=room_id,
        )

    @staticmethod
    async def is_member(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):
        return await RoomMemberRepository.is_member(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

    @staticmethod
    async def remove_member(
        session: AsyncSession,
        room_id: int,
        user_id: int,
    ):
        return await RoomMemberRepository.remove_member(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )
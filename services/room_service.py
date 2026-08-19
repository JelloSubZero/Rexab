from repositories.room_repository import RoomRepository
from utils.code_generator import generate_room_code
from sqlalchemy.ext.asyncio import AsyncSession


class RoomService:

    @staticmethod
    async def create_room(session, owner_id: int):

        while True:
            code = generate_room_code()

            exists = await RoomRepository.get_by_code(
                session,
                code,
            )

            if not exists:
                break

        return await RoomRepository.create(
            session,
            owner_id,
            code,
        )

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        room_id: int,
    ):
        return await RoomRepository.get_by_id(
            session,
            room_id,
        )

    @staticmethod
    async def get_by_code(
        session: AsyncSession,
        code: str,
    ):
        return await RoomRepository.get_by_code(
            session=session,
            code=code,
        )

    @staticmethod
    async def delete_room(
        session: AsyncSession,
        room_id: int,
    ) -> bool:

        return await RoomRepository.delete(
            session=session,
            room_id=room_id,
        )
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repository import UserRepository


class UserService:

    @staticmethod
    async def register(
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        first_name: str,
    ):

        user = await UserRepository.get_by_telegram_id(
            session,
            telegram_id,
        )

        if user:
            return user

        return await UserRepository.create(
            session,
            telegram_id,
            username,
            first_name,
        )
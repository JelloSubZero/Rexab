from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


class UserRepository:

    @staticmethod
    async def get_by_telegram_id(
        session: AsyncSession,
        telegram_id: int,
    ) -> User | None:

        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        first_name: str,
    ) -> User:

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        user_id: int,
    ) -> User | None:

        result = await session.execute(
            select(User).where(
                User.id == user_id
            )
        )

        return result.scalar_one_or_none()
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repository import UserRepository
from services.auth_service import AuthService


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

    @staticmethod
    async def register_with_password(
        session: AsyncSession,
        email: str,
        password: str,
        first_name: str,
    ):
        """
        Регистрация веб-пользователя по email/паролю.

        Возвращает None, если email уже занят.
        """

        existing = await UserRepository.get_by_email(
            session,
            email,
        )

        if existing is not None:
            return None

        password_hash = AuthService.hash_password(password)

        return await UserRepository.create(
            session,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
        )

    @staticmethod
    async def authenticate_with_password(
        session: AsyncSession,
        email: str,
        password: str,
    ):
        """
        Возвращает User при верном email/пароле, иначе None.

        None также возвращается для пользователей, у которых нет
        password_hash (например, если пользователь существует только
        как Telegram-аккаунт).
        """

        user = await UserRepository.get_by_email(
            session,
            email,
        )

        if user is None or user.password_hash is None:
            return None

        if not AuthService.verify_password(
            password,
            user.password_hash,
        ):
            return None

        return user
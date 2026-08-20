from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.errors import ApiError
from database.models import User
from database.session import AsyncSessionLocal
from repositories.user_repository import UserRepository
from services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    session: AsyncSession = Depends(get_session),
) -> User:

    if credentials is None:
        raise ApiError(
            401,
            "NOT_AUTHENTICATED",
            "Authentication required.",
        )

    user_id = AuthService.decode_access_token(
        credentials.credentials
    )

    if user_id is None:
        raise ApiError(
            401,
            "INVALID_TOKEN",
            "Invalid or expired token.",
        )

    user = await UserRepository.get_by_id(session, user_id)

    if user is None:
        raise ApiError(
            401,
            "INVALID_TOKEN",
            "User no longer exists.",
        )

    return user

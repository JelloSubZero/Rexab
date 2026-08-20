from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_session
from api.errors import ApiError
from api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TelegramAuthRequest,
    TokenResponse,
)
from api.schemas.user import UserResponse
from config import BOT_TOKEN
from database.models import User
from services.auth_service import AuthService
from services.telegram_auth_service import TelegramAuthService
from services.user_service import UserService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_token(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=AuthService.create_access_token(user.id),
        user=UserResponse.from_model(user),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    user = await UserService.register_with_password(
        session=session,
        email=body.email,
        password=body.password,
        first_name=body.first_name,
    )

    if user is None:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "EMAIL_TAKEN",
            "An account with this email already exists.",
        )

    await session.commit()

    return _issue_token(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    user = await UserService.authenticate_with_password(
        session=session,
        email=body.email,
        password=body.password,
    )

    if user is None:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_CREDENTIALS",
            "Incorrect email or password.",
        )

    return _issue_token(user)


@router.post("/telegram", response_model=TokenResponse)
async def login_with_telegram(
    body: TelegramAuthRequest,
    session: AsyncSession = Depends(get_session),
):
    if not BOT_TOKEN:
        raise ApiError(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "TELEGRAM_AUTH_NOT_CONFIGURED",
            "Telegram login is not configured on this server.",
        )

    is_valid = TelegramAuthService.verify(
        data=body.model_dump(exclude_none=True),
        bot_token=BOT_TOKEN,
    )

    if not is_valid:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_TELEGRAM_AUTH",
            "Telegram authentication data is invalid or expired.",
        )

    user = await UserService.register(
        session=session,
        telegram_id=body.id,
        username=body.username,
        first_name=body.first_name,
    )

    await session.commit()

    return _issue_token(user)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.from_model(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user),
):
    # Токены — stateless JWT без серверного хранения сессий, поэтому
    # отозвать их на сервере нельзя: клиент должен просто удалить
    # токен у себя. Эндпоинт существует ради единообразия API и для
    # будущей возможности добавить denylist/refresh-токены.
    return None

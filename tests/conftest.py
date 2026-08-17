import importlib.util

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


@pytest_asyncio.fixture
async def session():
    if importlib.util.find_spec("aiosqlite") is None:
        pytest.skip(
            "aiosqlite is required for database integration tests"
        )

    from database.models import User, Room, RoomMember  # noqa: F401
    from database.session import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as db_session:
        yield db_session
        await db_session.rollback()

    await engine.dispose()
import asyncio

from sqlalchemy import delete

from database.session import AsyncSessionLocal
from database.models import RoomHistory


async def cleanup():

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            delete(RoomHistory).where(
                RoomHistory.action.in_([
                    "test",
                    "test_service",
                ])
            )
        )

        await session.commit()

        print(
            f"✅ Удалено тестовых записей: "
            f"{result.rowcount}"
        )


if __name__ == "__main__":
    asyncio.run(cleanup())
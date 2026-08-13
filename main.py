from bot.app import main
from database.session import AsyncSessionLocal

from sqlalchemy import text


async def check_room_member_index():
    async with AsyncSessionLocal() as session:

        result = await session.execute(
            text("PRAGMA index_list('room_members')")
        )

        print("ROOM MEMBER INDEXES:")

        for row in result.fetchall():
            print(row)


if __name__ == "__main__":
    import asyncio

    asyncio.run(check_room_member_index())

    asyncio.run(main())
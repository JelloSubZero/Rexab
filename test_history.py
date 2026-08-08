import asyncio

from database.session import AsyncSessionLocal
from services.room_history_service import RoomHistoryService


async def test_history_service():

    async with AsyncSessionLocal() as session:

        # Создаём тестовую запись
        history = await RoomHistoryService.create(
            session=session,
            room_id=19,
            user_id=2,
            action="test_service",
            description="Проверка Service",
            amount=200.0,
        )

        print("✅ Service создал запись:")
        print("ID:", history.id)
        print("Room:", history.room_id)
        print("User:", history.user_id)
        print("Action:", history.action)
        print("Description:", history.description)
        print("Amount:", history.amount)

        # Получаем историю комнаты
        records = await RoomHistoryService.get_room_history(
            session=session,
            room_id=19,
        )

        print("\n📜 История через Service:")

        for record in records:
            print(
                record.id,
                record.action,
                record.description,
                record.amount,
            )


if __name__ == "__main__":
    asyncio.run(test_history_service())
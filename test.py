import asyncio

from database.session import AsyncSessionLocal

from services.settlement_service import SettlementService


ROOM_ID = 19

# Пример:
# user 2 должен user 1
DEBTOR_ID = 2
RECEIVER_ID = 1

AMOUNT = 100.0


async def main():

    async with AsyncSessionLocal() as session:

        print("=" * 40)
        print("1. СОЗДАНИЕ ПОГАШЕНИЯ")
        print("=" * 40)

        settlement = await SettlementService.create_settlement(
            session=session,
            room_id=ROOM_ID,
            from_user_id=DEBTOR_ID,
            to_user_id=RECEIVER_ID,
            amount=AMOUNT,
        )

        if settlement is None:
            print("❌ Не удалось создать погашение")
            return

        print("✅ Погашение создано:")
        print(f"ID: {settlement.id}")
        print(f"Room: {settlement.room_id}")
        print(f"From user: {settlement.from_user_id}")
        print(f"To user: {settlement.to_user_id}")
        print(f"Amount: {settlement.amount}")
        print(f"Status: {settlement.status}")

        print()
        print("=" * 40)
        print("2. ПРОВЕРКА ДОЛЖНИКА")
        print("=" * 40)

        result, status = await SettlementService.confirm_settlement(
            session=session,
            settlement_id=settlement.id,
            confirmer_user_id=DEBTOR_ID,
        )

        print(f"Result: {result}")
        print(f"Status: {status}")

        if status == "not_receiver":
            print(
                "✅ Должник не может подтвердить "
                "своё погашение."
            )
        else:
            print(
                "❌ ОШИБКА: должник смог "
                "подтвердить погашение!"
            )
            return

        print()
        print("=" * 40)
        print("3. ПРОВЕРКА ПОЛУЧАТЕЛЯ")
        print("=" * 40)

        result, status = await SettlementService.confirm_settlement(
            session=session,
            settlement_id=settlement.id,
            confirmer_user_id=RECEIVER_ID,
        )

        print(f"Result ID: {result.id if result else None}")
        print(f"Status: {status}")

        if status == "confirmed":
            print(
                "✅ Получатель успешно "
                "подтвердил погашение."
            )
        else:
            print(
                "❌ ОШИБКА: получатель "
                "не смог подтвердить."
            )
            return

        print()
        print("=" * 40)
        print("4. ПРОВЕРКА ПОВТОРНОГО ПОДТВЕРЖДЕНИЯ")
        print("=" * 40)

        result, status = await SettlementService.confirm_settlement(
            session=session,
            settlement_id=settlement.id,
            confirmer_user_id=RECEIVER_ID,
        )

        print(f"Result: {result}")
        print(f"Status: {status}")

        if status == "already_confirmed":
            print(
                "✅ Повторное подтверждение "
                "заблокировано."
            )
        else:
            print(
                "❌ ОШИБКА: погашение можно "
                "подтвердить повторно."
            )

        print()
        print("=" * 40)
        print("ТЕСТ ЗАВЕРШЁН")
        print("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())
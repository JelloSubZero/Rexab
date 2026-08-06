from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from database.init_db import init_db

from handlers.start import router as start_router
from handlers.room import router as room_router
from handlers.receipt import router as receipt_router
from handlers.receipt_callbacks import router as receipt_callbacks_router
from handlers.room_invite import router as room_invite_router
from handlers.split_bill import router as split_bill_router
from handlers.room_receipts import router as room_receipts_router
from handlers.room_view import router as room_view_router


async def main():
    # Создаем таблицы
    await init_db()

    # Создаем бота
    bot = Bot(BOT_TOKEN)

    # Создаем Dispatcher
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(room_invite_router)
    dp.include_router(room_receipts_router)
    dp.include_router(split_bill_router)
    dp.include_router(start_router)
    dp.include_router(room_router)
    dp.include_router(receipt_router)
    dp.include_router(receipt_callbacks_router)
    dp.include_router(room_view_router)
    print("✅ Rexab started")

    # Запускаем бота
    await dp.start_polling(bot)
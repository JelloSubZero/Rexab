import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from logging_config import setup_logging

from database.init_db import init_db

from handlers.start import router as start_router
from handlers.room import router as room_router
from handlers.receipt import router as receipt_router
from handlers.receipt_callbacks import router as receipt_callbacks_router
from handlers.room_invite import router as room_invite_router
from handlers.split_bill import router as split_bill_router
from handlers.room_receipts import router as room_receipts_router
from handlers.room_view import router as room_view_router
from handlers.room_members import router as room_members_router
from handlers.payment import router as payment_router
from handlers.room_history import router as room_history_router
from handlers.debt import router as debt_router
from handlers.settlement import router as settlement_router
from handlers.settlement_history import (
    router as settlement_history_router,
)

logger = logging.getLogger(__name__)


async def main():
    setup_logging()

    # Создаем таблицы
    await init_db()

    # Создаем бота
    bot = Bot(BOT_TOKEN)

    # Создаем Dispatcher
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(settlement_history_router)
    dp.include_router(settlement_router)
    dp.include_router(debt_router)
    dp.include_router(room_history_router)
    dp.include_router(payment_router)
    dp.include_router(room_members_router)
    dp.include_router(room_invite_router)
    dp.include_router(room_receipts_router)
    dp.include_router(split_bill_router)
    dp.include_router(start_router)
    dp.include_router(room_router)
    dp.include_router(receipt_router)
    dp.include_router(receipt_callbacks_router)
    dp.include_router(room_view_router)
    logger.info("Rexab started")

    # Запускаем бота
    await dp.start_polling(bot)
from aiogram import Dispatcher

from handlers.start import router as start_router
from handlers.room import router as room_router
from handlers.receipt import router as receipt_router


def register_routers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(room_router)
    dp.include_router(receipt_router)
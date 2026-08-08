from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def debt_optimize_menu(
    room_id: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="⬅️ Назад к расчёту",
        callback_data=f"debt_calculate:{room_id}",
    )

    builder.button(
        text="🏠 В меню комнаты",
        callback_data=f"room_view:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
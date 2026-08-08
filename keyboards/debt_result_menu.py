from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def debt_result_menu(
    room_id: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🧮 Изменить платежи",
        callback_data=f"room_split:{room_id}",
    )

    builder.button(
        text="⬅️ Назад",
        callback_data=f"room_view:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
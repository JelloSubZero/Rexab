from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def settlement_history_menu(
    room_id: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="⬅️ Назад",
        callback_data=(
            f"settlement_history_back:{room_id}"
        ),
    )

    builder.adjust(1)

    return builder.as_markup()
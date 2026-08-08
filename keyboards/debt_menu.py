from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def debt_menu(
    room_id: int,
    show_optimize: bool = True,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    if show_optimize:
        builder.button(
            text="⚡ Оптимизировать долги",
            callback_data=f"debt_optimize:{room_id}",
        )
    

    builder.button(
        text="⬅️ Назад",
        callback_data=f"room_view:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
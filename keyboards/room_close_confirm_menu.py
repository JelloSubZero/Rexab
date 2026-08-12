from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def room_close_confirm_menu(
    room_id: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔒 Да, закрыть",
        callback_data=f"room_close_confirm:{room_id}",
    )

    builder.button(
        text="⬅️ Отмена",
        callback_data=f"room_view:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
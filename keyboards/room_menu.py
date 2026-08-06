from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def room_menu(room_id: int) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📤 Пригласить",
        callback_data=f"room_invite:{room_id}",
    )

    builder.button(
        text="📄 Чеки",
        callback_data=f"room_receipts:{room_id}",
    )

    builder.button(
        text="👥 Участники",
        callback_data=f"room_members:{room_id}",
    )

    builder.button(
        text="🧮 Разделить счет",
        callback_data=f"room_split:{room_id}",
    )

    builder.adjust(2, 2)

    return builder.as_markup()
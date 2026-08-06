from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def room_receipts_menu(
    room_id: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="➕ Добавить чек",
        callback_data=f"add_receipt:{room_id}",
    )

    builder.button(
        text="🗑 Удалить чек",
        callback_data=f"delete_receipt:{room_id}",
    )

    builder.button(
        text="⬅️ Назад",
        callback_data=f"room_view:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
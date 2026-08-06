from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def receipt_menu(
    room_id: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🧾 Добавить еще чек",
        callback_data=f"add_receipt:{room_id}",
    )

    builder.button(
        text="✅ Завершить добавление",
        callback_data=f"finish_receipts:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
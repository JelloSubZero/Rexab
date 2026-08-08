from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def payment_delete_menu(
    payment_id: int,
    room_id: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="❌ Да, удалить",
        callback_data=(
            f"payment_delete_confirm:"
            f"{payment_id}:{room_id}"
        ),
    )

    builder.button(
        text="⬅️ Отмена",
        callback_data=f"payment_manage:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
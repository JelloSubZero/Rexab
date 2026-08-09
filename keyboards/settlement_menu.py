from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def settlement_menu(
    room_id: int,
    settlement_id: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="💰 Я получил деньги",
        callback_data=(
            f"settlement_confirm:"
            f"{settlement_id}:"
            f"{room_id}"
        ),
    )

    builder.button(
            text="⬅️ Назад",
            callback_data=f"room_view:{room_id}",
        )

    builder.adjust(1)

    return builder.as_markup()
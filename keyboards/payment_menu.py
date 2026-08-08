from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def payment_menu(
    room_id: int,
    members,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    for member in members:

        name = (
            member.user.first_name
            if member.user
            else "Неизвестный"
        )

        builder.button(
            text=f"💳 {name}",
            callback_data=(
                f"payment_user:{room_id}:{member.user_id}"
            ),
        )

    builder.button(
        text="✅ Готово",
        callback_data=f"payment_done:{room_id}",
    )

    builder.button(
        text="⬅️ Назад",
        callback_data=f"room_view:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
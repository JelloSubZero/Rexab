from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def payment_manage_menu(
    room_id: int,
    payments,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    for payment in payments:

        name = (
            payment.user.first_name
            if payment.user
            else "Неизвестный"
        )

        description = (
            payment.description
            if payment.description
            else "Расход"
        )

        builder.button(
            text=(
                f"🗑 {name} — "
                f"{payment.amount:.2f} zł "
                f"({description})"
            ),
            callback_data=f"payment_delete:{payment.id}",
        )

    builder.button(
    text="➕ Добавить платёж",
    callback_data=f"payment_add:{room_id}",
    )

    builder.button(
        text="⬅️ Назад",
        callback_data=f"room_view:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
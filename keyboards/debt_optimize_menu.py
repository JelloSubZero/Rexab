from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def debt_optimize_menu(
    room_id: int,
    transfers=None,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    if transfers:

        for transfer in transfers:

            from_user_id = transfer["from_user_id"]
            to_user_id = transfer["to_user_id"]
            amount = transfer["amount"]

            builder.button(
                text=(
                    f"💰 Погашение "
                    f"{amount:.2f} zł"
                ),
                callback_data=(
                    f"settlement_create:"
                    f"{room_id}:"
                    f"{from_user_id}:"
                    f"{to_user_id}:"
                    f"{amount}"
                ),
            )

    builder.button(
        text="⬅️ Назад",
        callback_data=f"debt_calculate:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
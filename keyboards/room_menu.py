from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def room_menu(
    room_id: int,
    is_owner: bool = False,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="💳 Платежи",
        callback_data=f"payment_manage:{room_id}",
    )

    builder.button(
        text="👥 Участники",
        callback_data=f"room_members:{room_id}",
    )

    builder.button(
        text="📤 Пригласить",
        callback_data=f"room_invite:{room_id}",
    )

    builder.button(
        text="📄 Чеки",
        callback_data=f"room_receipts:{room_id}",
    )

    builder.button(
        text="📜 История",
        callback_data=f"room_history:{room_id}",
    )

    builder.button(
        text="💰 История погашений",
        callback_data=f"settlement_history:{room_id}",
    )

    if is_owner:
        builder.button(
            text="🔒 Закрыть комнату",
            callback_data=f"room_close:{room_id}",
        )

    builder.adjust(1, 2, 2, 1, 1)

    return builder.as_markup()
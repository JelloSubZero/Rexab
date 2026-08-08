from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def room_members_menu(
    room_id: int,
    members=None,
    owner_id: int | None = None,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    if members and owner_id is not None:

        for member in members:

            if member.user_id == owner_id:
                continue

            name = (
                member.user.first_name
                if member.user
                else "Неизвестный"
            )

            builder.button(
                text=f"❌ Удалить {name}",
                callback_data=f"remove_member:{room_id}:{member.user_id}",
            )

    builder.button(
        text="⬅️ Назад",
        callback_data=f"room_view:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
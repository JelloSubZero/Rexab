from aiogram.utils.keyboard import InlineKeyboardBuilder


def room_history_menu(room_id: int):

    builder = InlineKeyboardBuilder()

    builder.button(
        text="⬅️ Назад",
        callback_data=f"room_view:{room_id}",
    )

    builder.adjust(1)

    return builder.as_markup()
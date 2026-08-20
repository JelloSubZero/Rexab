from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu():
    builder = ReplyKeyboardBuilder()

    builder.button(text="➕ Создать чек")

    builder.adjust(1)

    return builder.as_markup(
        resize_keyboard=True
    )
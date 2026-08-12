from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def closed_room_menu(
    room_id: int,
    transfers=None,
    current_user_id: int | None = None,
    pending_for_debtor=None,
    pending_for_receiver=None,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    transfers = transfers or []
    pending_for_debtor = pending_for_debtor or []
    pending_for_receiver = pending_for_receiver or []

    # -----------------------------
    # ДОЛЖНИК
    # -----------------------------

    if current_user_id is not None:

        for transfer in transfers:

            if transfer["from_user_id"] != current_user_id:
                continue

            to_user_id = transfer["to_user_id"]
            amount = float(transfer["amount"])

            already_pending = any(
                item.to_user_id == to_user_id
                and abs(
                    float(item.amount) - amount
                ) <= 0.01
                for item in pending_for_debtor
            )

            if already_pending:
                continue

            builder.button(
                text=(
                    f"💸 Я оплатил "
                    f"{amount:.2f} zł"
                ),
                callback_data=(
                    f"settlement_create:"
                    f"{room_id}:"
                    f"{current_user_id}:"
                    f"{to_user_id}:"
                    f"{amount}"
                ),
            )

    # -----------------------------
    # ПОЛУЧАТЕЛЬ
    # -----------------------------

    for settlement in pending_for_receiver:

        builder.button(
            text=(
                f"✅ Получил "
                f"{float(settlement.amount):.2f} zł"
            ),
            callback_data=(
                f"settlement_confirm:"
                f"{settlement.id}"
            ),
        )

    builder.adjust(1)

    return builder.as_markup()
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from repositories.user_repository import UserRepository

from services.room_access_service import RoomAccessService
from services.room_view_service import RoomViewService
from services.settlement_service import SettlementService

from keyboards.room_menu import room_menu
from keyboards.settlement_history_menu import (
    settlement_history_menu,
)


router = Router()


# ========================================
# ИСТОРИЯ ПОГАШЕНИЙ
# ========================================

@router.callback_query(
    F.data.startswith("settlement_history:")
)
async def settlement_history(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        # --------------------------------
        # ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
        # --------------------------------

        current_user = (
            await UserRepository.get_by_telegram_id(
                session=session,
                telegram_id=callback.from_user.id,
            )
        )

        if current_user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПРОВЕРКА ДОСТУПА
        # --------------------------------

        has_access = (
            await RoomAccessService.check_access(
                session=session,
                room_id=room_id,
                user_id=current_user.id,
            )
        )

        if not has_access:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПОЛУЧАЕМ ИСТОРИЮ
        # --------------------------------

        settlements = (
            await SettlementService.get_room_history(
                session=session,
                room_id=room_id,
            )
        )

        # --------------------------------
        # ЕСЛИ ИСТОРИИ НЕТ
        # --------------------------------

        if not settlements:

            text = (
                "💰 <b>История погашений</b>\n\n"
                "Пока погашений нет."
            )

            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=settlement_history_menu(
                    room_id=room_id,
                ),
            )

            await callback.answer()
            return

        # --------------------------------
        # ПОЛУЧАЕМ ИМЕНА ПОЛЬЗОВАТЕЛЕЙ
        # --------------------------------

        users = {}

        user_ids = set()

        for settlement in settlements:

            user_ids.add(
                settlement.from_user_id
            )

            user_ids.add(
                settlement.to_user_id
            )

        for user_id in user_ids:

            user = await UserRepository.get_by_id(
                session=session,
                user_id=user_id,
            )

            if user:

                users[user_id] = (
                    user.first_name
                    or user.username
                    or "Пользователь"
                )

        # --------------------------------
        # ФОРМИРУЕМ ИСТОРИЮ
        # --------------------------------

        history_text = ""

        for settlement in settlements:

            from_name = users.get(
                settlement.from_user_id,
                "Неизвестный",
            )

            to_name = users.get(
                settlement.to_user_id,
                "Неизвестный",
            )

            amount = float(
                settlement.amount
            )

            # --------------------------------
            # СТАТУС
            # --------------------------------

            if settlement.status == "confirmed":

                status_text = (
                    "✅ <b>Погашено</b>"
                )

                date = (
                    settlement.confirmed_at
                    or settlement.created_at
                )

            else:

                status_text = (
                    "⏳ <b>Ожидает подтверждения</b>"
                )

                date = settlement.created_at

            # --------------------------------
            # ДАТА
            # --------------------------------

            if date:

                date_text = date.strftime(
                    "%d.%m.%Y %H:%M"
                )

            else:

                date_text = "—"

            # --------------------------------
            # ЗАПИСЬ
            # --------------------------------

            history_text += (
                f"• <b>{from_name}</b> → "
                f"<b>{to_name}</b>\n"
                f"  💰 <b>{amount:.2f} zł</b>\n"
                f"  {status_text}\n"
                f"  🕒 {date_text}\n\n"
            )

        # --------------------------------
        # ИТОГОВЫЙ ТЕКСТ
        # --------------------------------

        text = (
            "💰 <b>История погашений</b>\n\n"
            f"{history_text}"
        )

        # --------------------------------
        # ВАЖНО:
        # РЕДАКТИРУЕМ СТАРОЕ СООБЩЕНИЕ
        # --------------------------------

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=settlement_history_menu(
                room_id=room_id,
            ),
        )

        await callback.answer()


# ========================================
# НАЗАД В МЕНЮ КОМНАТЫ
# ========================================

@router.callback_query(
    F.data.startswith(
        "settlement_history_back:"
    )
)
async def settlement_history_back(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        # --------------------------------
        # ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
        # --------------------------------

        current_user = (
            await UserRepository.get_by_telegram_id(
                session=session,
                telegram_id=callback.from_user.id,
            )
        )

        if current_user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПРОВЕРКА ДОСТУПА
        # --------------------------------

        has_access = (
            await RoomAccessService.check_access(
                session=session,
                room_id=room_id,
                user_id=current_user.id,
            )
        )

        if not has_access:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПОЛУЧАЕМ ДАННЫЕ КОМНАТЫ
        # --------------------------------

        room_data = await RoomViewService.build(
            session=session,
            room_id=room_id,
        )

        if not room_data:

            await callback.answer(
                "❌ Комната не найдена.",
                show_alert=True,
            )
            return

        room = room_data["room"]
        total = room_data["total"] or 0
        members = room_data["members"]

        # --------------------------------
        # СПИСОК УЧАСТНИКОВ
        # --------------------------------

        members_text = ""

        for index, member in enumerate(
            members,
            start=1,
        ):

            name = (
                member.user.first_name
                if member.user
                else "Неизвестный"
            )

            if member.user_id == room.owner_id:
                name += " 👑"

            members_text += (
                f"{index}. {name}\n"
            )

        # --------------------------------
        # МЕНЮ КОМНАТЫ
        # --------------------------------

        text = (
            "🏠 <b>Комната</b>\n\n"

            "🔑 Код:\n"
            f"<code>{room.code}</code>\n\n"

            "💰 Общая сумма:\n"
            f"<b>{total:.2f} zł</b>\n\n"

            "👥 Участников: "
            f"<b>{len(members)}</b>\n\n"

            f"{members_text}"
        )

        # --------------------------------
        # РЕДАКТИРУЕМ ТО ЖЕ СООБЩЕНИЕ
        # --------------------------------

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=room_menu(
                room_id=room.id,
            ),
        )

        await callback.answer()
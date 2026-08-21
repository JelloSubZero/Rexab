import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from repositories.user_repository import UserRepository

from services.room_service import RoomService
from services.room_member_service import RoomMemberService
from services.settlement_permission_service import (
    SettlementPermission,
    SettlementPermissionService,
)
from services.settlement_service import SettlementService
from services.room_payment_service import RoomPaymentService
from services.debt_service import DebtService
from services.anchor_service import AnchorService, build_closed_screen, build_menu_screen
from services.receipt_service import ReceiptService
from database.models import RoomStatus

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(
    F.data.startswith("settlement_create:")
)
async def settlement_create(
    callback: CallbackQuery,
    bot,
):
    _, room_id_str, from_user_id_str, to_user_id_str, amount_str = (
        callback.data.split(":")
    )

    room_id = int(room_id_str)
    from_user_id = int(from_user_id_str)
    to_user_id = int(to_user_id_str)
    requested_amount = float(amount_str)

    async with AsyncSessionLocal() as session:

        # --------------------------------
        # ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
        # --------------------------------

        current_user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=callback.from_user.id,
        )

        if current_user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПРОВЕРКА ДОСТУПА К КОМНАТЕ
        # --------------------------------

        permission = await SettlementPermissionService.can_create(
            session=session,
            room_id=room_id,
            actor_user_id=current_user.id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
        )

        if permission == SettlementPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        if permission == SettlementPermission.DEBTOR_NOT_MEMBER:
            await callback.answer(
                "❌ Должник больше не является "
                "участником комнаты.",
                show_alert=True,
            )
            return

        if permission == SettlementPermission.RECEIVER_NOT_MEMBER:
            await callback.answer(
                "❌ Получатель больше не является "
                "участником комнаты.",
                show_alert=True,
            )
            return

        if permission == SettlementPermission.SAME_USER:
            await callback.answer(
                "❌ Нельзя создать погашение "
                "самому себе.",
                show_alert=True,
            )
            return

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )
        # --------------------------------
        # ПОЛУЧАЕМ АКТУАЛЬНЫЕ ПЛАТЕЖИ
        # --------------------------------

        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        # --------------------------------
        # ПОЛУЧАЕМ ПОДТВЕРЖДЁННЫЕ ПОГАШЕНИЯ
        # --------------------------------

        settlements = await SettlementService.get_confirmed_for_room(
            session=session,
            room_id=room_id,
        )

        # --------------------------------
        # ПОВТОРНО РАССЧИТЫВАЕМ ДОЛГИ
        # С УЧЁТОМ ПОГАШЕНИЙ
        # --------------------------------

        transfers = DebtService.calculate(
            members=members,
            payments=payments,
            settlements=settlements,
        )

        # --------------------------------
        # ИЩЕМ НУЖНЫЙ ПЕРЕВОД
        # --------------------------------

        actual_amount = None

        for transfer in transfers:

            if (
                transfer["from_user_id"] == from_user_id
                and transfer["to_user_id"] == to_user_id
            ):
                actual_amount = float(
                    transfer["amount"]
                )
                break

        if actual_amount is None:
            await callback.answer(
                "❌ Этот долг больше не существует.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПРОВЕРЯЕМ СУММУ
        # --------------------------------

        if abs(actual_amount - requested_amount) > 0.01:
            await callback.answer(
                "⚠️ Сумма долга изменилась. "
                "Обновите расчёт.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПРОВЕРЯЕМ, НЕТ ЛИ УЖЕ PENDING
        # --------------------------------

        pending = (
            await SettlementService.get_pending_for_receiver(
                session=session,
                room_id=room_id,
                user_id=to_user_id,
            )
        )

        for item in pending:

            if (
                item.from_user_id == from_user_id
                and abs(
                    float(item.amount) - actual_amount
                ) <= 0.01
            ):
                await callback.answer(
                    "ℹ️ Это погашение уже ожидает "
                    "подтверждения получателя.",
                    show_alert=True,
                )
                return

        # --------------------------------
        # СОЗДАЁМ PENDING SETTLEMENT
        # --------------------------------

        settlement = (
            await SettlementService.create_settlement(
                session=session,
                room_id=room_id,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=actual_amount,
            )
        )

        if settlement is None:
            await callback.answer(
                "❌ Не удалось создать погашение.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПОЛУЧАЕМ ДАННЫЕ ПОЛЬЗОВАТЕЛЕЙ
        # --------------------------------

        debtor = await UserRepository.get_by_id(
            session=session,
            user_id=from_user_id,
        )

        receiver = await UserRepository.get_by_id(
            session=session,
            user_id=to_user_id,
        )

        debtor_name = (
            debtor.first_name
            if debtor
            else "Пользователь"
        )

        receiver_name = (
            receiver.first_name
            if receiver
            else "Пользователь"
        )

        # --------------------------------
        # ОБНОВЛЯЕМ ЯКОРНЫЕ СООБЩЕНИЯ ОБЕИХ СТОРОН
        # --------------------------------

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        if room is None:
            await callback.answer(
                "❌ Комната не найдена.",
                show_alert=True,
            )
            return

        confirmed_settlements = (
            await SettlementService.get_confirmed_for_room(
                session=session,
                room_id=room_id,
            )
        )

        transfers = DebtService.calculate(
            members=members,
            payments=payments,
            settlements=confirmed_settlements,
        )

        room_total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        async def render_room_screen(member_user_id):

            if room.status == RoomStatus.CLOSED.value:

                pending_for_debtor = (
                    await SettlementService.get_pending_for_debtor(
                        session=session,
                        room_id=room_id,
                        user_id=member_user_id,
                    )
                )

                pending_for_receiver = (
                    await SettlementService.get_pending_for_receiver(
                        session=session,
                        room_id=room_id,
                        user_id=member_user_id,
                    )
                )

                return build_closed_screen(
                    room=room,
                    members=members,
                    transfers=transfers,
                    user_id=member_user_id,
                    pending_for_debtor=pending_for_debtor,
                    pending_for_receiver=pending_for_receiver,
                )

            return build_menu_screen(
                room=room,
                total=room_total,
                members=members,
                is_owner=(member_user_id == room.owner_id),
            )

        for member_user_id in (from_user_id, to_user_id):
            text_for_member, keyboard_for_member = await render_room_screen(
                member_user_id
            )

            await AnchorService.render(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=member_user_id,
                text=text_for_member,
                keyboard=keyboard_for_member,
            )

        # --------------------------------
        # PUSH-УВЕДОМЛЕНИЕ ПОЛУЧАТЕЛЮ
        # --------------------------------

        if receiver is not None:
            await AnchorService.ping(
                bot=bot,
                chat_id=receiver.telegram_id,
                text=(
                    "🔔 <b>Ожидается погашение</b>\n\n"
                    f"👤 <b>{debtor_name}</b> отметил(а), что "
                    f"оплатил(а) вам <b>{actual_amount:.2f} zł</b>.\n\n"
                    "Откройте комнату, чтобы подтвердить получение."
                ),
            )

        # --------------------------------
        # ФИКСИРУЕМ TRANSACTION
        # --------------------------------

        await session.commit()

    await callback.answer(
        "✅ Ожидается подтверждение получателя."
    )


# ============================================================
# ПОДТВЕРЖДЕНИЕ ПОГАШЕНИЯ
# ============================================================

@router.callback_query(
    F.data.startswith("settlement_confirm:")
)
async def settlement_confirm(
    callback: CallbackQuery,
    bot,
):
    settlement_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

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

        settlement = await SettlementService.get_by_id(
            session=session,
            settlement_id=settlement_id,
        )

        if settlement is None:
            await callback.answer(
                "❌ Погашение не найдено.",
                show_alert=True,
            )
            return

        room_id = settlement.room_id

        permission = await SettlementPermissionService.can_confirm(
            session=session,
            room_id=room_id,
            settlement_id=settlement_id,
            actor_user_id=current_user.id,
        )

        if permission == SettlementPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        if permission == SettlementPermission.SETTLEMENT_NOT_FOUND:
            await callback.answer(
                "❌ Погашение не найдено.",
                show_alert=True,
            )
            return

        if permission == SettlementPermission.WRONG_ROOM:
            await callback.answer(
                "❌ Погашение относится к другой комнате.",
                show_alert=True,
            )
            return

        if permission == SettlementPermission.NOT_RECEIVER:
            await callback.answer(
                "❌ Только получатель может "
                "подтвердить погашение.",
                show_alert=True,
            )
            return

        debtor = await UserRepository.get_by_id(
            session=session,
            user_id=settlement.from_user_id,
        )

        confirmed, status = (
            await SettlementService.confirm_settlement(
                session=session,
                settlement_id=settlement_id,
                confirmer_user_id=current_user.id,
            )
        )

        if status == "already_confirmed":
            await callback.answer(
                "ℹ️ Это погашение уже подтверждено.",
                show_alert=True,
            )
            return

        if status == "not_receiver":
            await callback.answer(
                "❌ Только получатель может "
                "подтвердить погашение.",
                show_alert=True,
            )
            return

        if status != "confirmed" or confirmed is None:
            await callback.answer(
                "❌ Не удалось подтвердить погашение.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ОБНОВЛЯЕМ ЯКОРНЫЕ СООБЩЕНИЯ ОБЕИХ СТОРОН
        # --------------------------------

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        if room is None:
            await callback.answer(
                "❌ Комната не найдена.",
                show_alert=True,
            )
            return

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        confirmed_settlements = (
            await SettlementService.get_confirmed_for_room(
                session=session,
                room_id=room_id,
            )
        )

        transfers = DebtService.calculate(
            members=members,
            payments=payments,
            settlements=confirmed_settlements,
        )

        room_total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        async def render_room_screen(member_user_id):

            if room.status == RoomStatus.CLOSED.value:

                pending_for_debtor = (
                    await SettlementService.get_pending_for_debtor(
                        session=session,
                        room_id=room_id,
                        user_id=member_user_id,
                    )
                )

                pending_for_receiver = (
                    await SettlementService.get_pending_for_receiver(
                        session=session,
                        room_id=room_id,
                        user_id=member_user_id,
                    )
                )

                return build_closed_screen(
                    room=room,
                    members=members,
                    transfers=transfers,
                    user_id=member_user_id,
                    pending_for_debtor=pending_for_debtor,
                    pending_for_receiver=pending_for_receiver,
                )

            return build_menu_screen(
                room=room,
                total=room_total,
                members=members,
                is_owner=(member_user_id == room.owner_id),
            )

        for member_user_id in (settlement.from_user_id, settlement.to_user_id):
            text_for_member, keyboard_for_member = await render_room_screen(
                member_user_id
            )

            await AnchorService.render(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=member_user_id,
                text=text_for_member,
                keyboard=keyboard_for_member,
            )

        # --------------------------------
        # PUSH-УВЕДОМЛЕНИЕ ДОЛЖНИКУ
        # --------------------------------

        if debtor is not None:
            await AnchorService.ping(
                bot=bot,
                chat_id=debtor.telegram_id,
                text=(
                    "✅ <b>Погашение подтверждено</b>\n\n"
                    f"Получатель подтвердил получение "
                    f"<b>{float(settlement.amount):.2f} zł</b>."
                ),
            )

        # --------------------------------
        # ПРОВЕРЯЕМ, ПОЛНОСТЬЮ ЛИ ПОГАШЕНА КОМНАТА
        # --------------------------------

        fully_settled = len(transfers) == 0

        if fully_settled and room.status == "closed":
            await AnchorService.finalize(
                bot=bot,
                session=session,
                room_id=room_id,
            )

        await session.commit()

    await callback.answer(
        "✅ Деньги получены."
    )

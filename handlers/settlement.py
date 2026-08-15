from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.room_message_service import RoomMessageService
from services.room_view_service import RoomViewService

from database.session import AsyncSessionLocal

from repositories.user_repository import UserRepository

from services.room_access_service import RoomAccessService
from services.room_member_service import RoomMemberService
from services.settlement_service import SettlementService
from services.notification_service import NotificationService
from services.room_payment_service import RoomPaymentService
from services.debt_service import DebtService
from services.room_service import RoomService
from keyboards.settlement_menu import settlement_menu


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

        has_access = await RoomAccessService.check_access(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not has_access:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПОЛУЧАЕМ УЧАСТНИКОВ
        # --------------------------------

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        member_ids = {
            member.user_id
            for member in members
        }

        # --------------------------------
        # ПРОВЕРЯЕМ УЧАСТНИКОВ ПЕРЕВОДА
        # --------------------------------

        if from_user_id not in member_ids:
            await callback.answer(
                "❌ Должник больше не является "
                "участником комнаты.",
                show_alert=True,
            )
            return

        if to_user_id not in member_ids:
            await callback.answer(
                "❌ Получатель больше не является "
                "участником комнаты.",
                show_alert=True,
            )
            return

        if from_user_id == to_user_id:
            await callback.answer(
                "❌ Нельзя создать погашение "
                "самому себе.",
                show_alert=True,
            )
            return

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
        # ОТПРАВЛЯЕМ ПОЛУЧАТЕЛЮ
        # --------------------------------

        try:

            await RoomMessageService.send(
                bot=bot,
                session=session,
                room_id=room_id,
                chat_id=receiver.telegram_id,
                text=(
                    "💰 <b>Ожидается погашение</b>\n\n"
                    f"👤 <b>{debtor_name}</b> "
                    "должен вам:\n\n"
                    f"💵 <b>{actual_amount:.2f} zł</b>\n\n"
                    "После получения денег "
                    "подтвердите погашение:"
                ),
                parse_mode="HTML",
                reply_markup=settlement_menu(
                    room_id=room_id,
                    settlement_id=settlement.id,
                ),
            )

        except Exception as e:

            print(
                "❌ Не удалось отправить "
                f"уведомление получателю: {e}"
            )
        # --------------------------------
        # УВЕДОМЛЯЕМ ДОЛЖНИКА
        # --------------------------------

        if debtor is not None:

            try:

                await RoomMessageService.send(
                    bot=bot,
                    session=session,
                    room_id=room_id,
                    chat_id=debtor.telegram_id,
                    text=(
                        "💸 <b>Ожидается подтверждение</b>\n\n"
                        f"Вы должны <b>{receiver_name}</b>:\n\n"
                        f"💰 <b>{actual_amount:.2f} zł</b>\n\n"
                        "После передачи денег "
                        "получатель должен подтвердить "
                        "погашение."
                    ),
                    parse_mode="HTML",
                )

            except Exception as e:

                print(
                    "❌ Не удалось отправить "
                    f"уведомление должнику: {e}"
                )

        # --------------------------------
        # ФИКСИРУЕМ TRANSACTION
        # --------------------------------

        await session.commit()

    # --------------------------------
    # ОБНОВЛЯЕМ ЭКРАН
    # --------------------------------

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
    _, settlement_id_str, room_id_str = (
        callback.data.split(":")
    )

    settlement_id = int(settlement_id_str)
    room_id = int(room_id_str)

    async with AsyncSessionLocal() as session:

        # ----------------------------------------------------
        # ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # ПРОВЕРЯЕМ ДОСТУП К КОМНАТЕ
        # ----------------------------------------------------

        has_access = await RoomAccessService.check_access(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not has_access:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        # ----------------------------------------------------
        # ПОЛУЧАЕМ ПОГАШЕНИЕ
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # ПРОВЕРЯЕМ КОМНАТУ
        # ----------------------------------------------------

        if settlement.room_id != room_id:
            await callback.answer(
                "❌ Погашение относится к другой комнате.",
                show_alert=True,
            )
            return

        # ----------------------------------------------------
        # ПРОВЕРЯЕМ, ЧТО ПОЛЬЗОВАТЕЛЬ —
        # ПОЛУЧАТЕЛЬ ДЕНЕГ
        # ----------------------------------------------------

        if settlement.to_user_id != current_user.id:
            await callback.answer(
                "❌ Только получатель может "
                "подтвердить погашение.",
                show_alert=True,
            )
            return

        # ----------------------------------------------------
        # СОХРАНЯЕМ ДАННЫЕ ДО ПОДТВЕРЖДЕНИЯ
        # ----------------------------------------------------

        debtor = await UserRepository.get_by_id(
            session=session,
            user_id=settlement.from_user_id,
        )

        receiver = await UserRepository.get_by_id(
            session=session,
            user_id=settlement.to_user_id,
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

        amount = float(settlement.amount)

        # ----------------------------------------------------
        # ПОДТВЕРЖДАЕМ ПОГАШЕНИЕ
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # УВЕДОМЛЯЕМ ДОЛЖНИКА
        # ----------------------------------------------------

        try:
            sent_message = await bot.send_message(
                chat_id=debtor.telegram_id,
                text=(
                    "✅ <b>Погашение подтверждено</b>\n\n"
                    f"👤 <b>{receiver_name}</b> "
                    "подтвердил получение денег.\n\n"
                    f"💰 Сумма: "
                    f"<b>{amount:.2f} zł</b>\n\n"
                    "💸 Этот долг отмечен как погашенный."
                ),
                parse_mode="HTML",
            )

            await RoomMessageService.save(
                session=session,
                room_id=room_id,
                chat_id=debtor.telegram_id,
                message_id=sent_message.message_id,
            )

        except Exception as e:
            print(
                "❌ Не удалось отправить "
                f"уведомление должнику: {e}"
            )

        # ----------------------------------------------------
        # ОБНОВЛЯЕМ СООБЩЕНИЕ ПОЛУЧАТЕЛЯ
        # ----------------------------------------------------

        await callback.message.edit_text(
            (
                "✅ <b>Погашение подтверждено</b>\n\n"
                f"👤 <b>{debtor_name}</b> "
                "передал вам деньги.\n\n"
                f"💰 Сумма: "
                f"<b>{amount:.2f} zł</b>\n\n"
                "💚 Долг закрыт."
            ),
            parse_mode="HTML",
        )

          # ----------------------------------------------------
        # РАССЧИТЫВАЕМ ТЕКУЩИЕ ДОЛГИ
        # ----------------------------------------------------

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        # ----------------------------------------------------
        # ПОЛУЧАЕМ ПОДТВЕРЖДЁННЫЕ ПОГАШЕНИЯ
        # ----------------------------------------------------

        confirmed_settlements = (
            await SettlementService.get_confirmed_for_room(
                session=session,
                room_id=room_id,
            )
        )

        # ----------------------------------------------------
        # РАССЧИТЫВАЕМ ДОЛГИ С УЧЁТОМ ПОГАШЕНИЙ
        # ----------------------------------------------------

        transfers = DebtService.calculate(
            members=members,
            payments=payments,
            settlements=confirmed_settlements,
        )

        # ----------------------------------------------------
        # ЕСЛИ ДОЛГОВ БОЛЬШЕ НЕТ —
        # КОМНАТА ЗАВЕРШЕНА
        # ----------------------------------------------------

        if not transfers:

            participants = []

            for member in members:

                user = await UserRepository.get_by_id(
                    session=session,
                    user_id=member.user_id,
                )

                if user is not None:
                    participants.append(user)

            # --------------------------------
            # --------------------------------
            # УДАЛЯЕМ ОСНОВНЫЕ СООБЩЕНИЯ КОМНАТЫ
            # --------------------------------

            # Получаем все основные сообщения комнаты
            room_views = await RoomViewService.get_views(
                session=session,
                room_id=room_id,
            )

            # Удаляем основное сообщение комнаты у каждого пользователя
            for room_view in room_views:
                try:
                    await bot.delete_message(
                        chat_id=room_view.chat_id,
                        message_id=room_view.message_id,
                    )
                except Exception as e:
                    print(
                        f"❌ Не удалось удалить RoomView: "
                        f"chat={room_view.chat_id}, "
                        f"message={room_view.message_id}: {e}"
                    )

            # --------------------------------
            # УДАЛЯЕМ ДОПОЛНИТЕЛЬНЫЕ СООБЩЕНИЯ
            # --------------------------------

            await RoomMessageService.delete_all(
                bot=bot,
                session=session,
                room_id=room_id,
            )

            # --------------------------------
            # УДАЛЯЕМ КОМНАТУ ИЗ БД
            # --------------------------------

            deleted = await RoomService.delete_room(
                session=session,
                room_id=room_id,
            )

            # --------------------------------
            # УВЕДОМЛЯЕМ УЧАСТНИКОВ
            # --------------------------------

            if deleted:
                for user in participants:
                    try:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=(
                                "🏁 <b>Комната завершена</b>\n\n"
                                "Все долги погашены.\n"
                                "Комната была автоматически удалена."
                            ),
                            parse_mode="HTML",
                        )

                    except Exception as e:
                        print(
                            "❌ Не удалось уведомить "
                            f"пользователя {user.id}: {e}"
                        )

                await callback.answer(
                    "🏁 Все долги погашены. Комната удалена."
                )

                return

    
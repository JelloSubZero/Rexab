from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.payment_delete_menu import payment_delete_menu
from services.room_member_service import RoomMemberService
from services.room_history_service import RoomHistoryService
from services.notification_service import NotificationService
from services.room_service import RoomService
from services.receipt_service import ReceiptService
from services.anchor_service import AnchorService, build_menu_screen
from services.payment_permission_service import (
    PaymentPermission,
    PaymentPermissionService,
)


from database.session import AsyncSessionLocal
from services.split_bill_service import SplitBillService
from services.room_payment_service import RoomPaymentService

from repositories.user_repository import UserRepository

from states.payment_state import PaymentState
from services.debt_service import DebtService

from keyboards.payment_manage_menu import payment_manage_menu


router = Router()


def _payments_text(payments, split) -> str:
    header = "💳 <b>Платежи комнаты</b>\n\n"

    if split["count"]:
        header += (
            f"🧾 Расходы по чекам: <b>{split['total']:.2f} zł</b>\n"
            f"👤 На человека: <b>{split['per_person']:.2f} zł</b>\n\n"
        )

    if not payments:
        return header + "Пока нет добавленных платежей."

    lines = ""
    total = 0

    for payment in payments:
        name = (
            payment.user.first_name
            if payment.user
            else "Неизвестный"
        )
        description = payment.description or "Расход"
        total += payment.amount

        lines += (
            f"• <b>{name}</b> — "
            f"<b>{payment.amount:.2f} zł</b>\n"
            f"  📝 {description}\n\n"
        )

    return (
        header
        + lines
        + "────────────────\n"
        + f"💰 Оплачено: <b>{total:.2f} zł</b>"
    )


@router.callback_query(
    F.data.startswith("payment_delete:")
)
async def payment_delete(
    callback: CallbackQuery,
):
    payment_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        payment = await RoomPaymentService.get_payment(
            session=session,
            payment_id=payment_id,
        )

        if payment is None:
            await callback.answer(
                "❌ Платёж не найден.",
                show_alert=True,
            )
            return

        room_id = payment.room_id

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

        permission = await PaymentPermissionService.can_manage(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if permission == PaymentPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        payer_name = (
            payment.user.first_name
            if payment.user
            else "Неизвестный"
        )

        description = (
            payment.description
            if payment.description
            else "Расход"
        )

        amount = payment.amount

    async with AsyncSessionLocal() as session:

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=(
                "🗑 <b>Удалить платёж?</b>\n\n"
                f"💳 Плательщик: <b>{payer_name}</b>\n"
                f"💰 Сумма: <b>{amount:.2f} zł</b>\n"
                f"📝 Расход: <b>{description}</b>\n\n"
                "Вы уверены?"
            ),
            keyboard=payment_delete_menu(
                payment_id=payment_id,
                room_id=room_id,
            ),
        )

        await session.commit()

    await callback.answer()

@router.callback_query(
    F.data.startswith("payment_delete_confirm:")
)
async def payment_delete_confirm(
    callback: CallbackQuery,
    bot: Bot,
):
    _, payment_id_str, room_id_str = callback.data.split(":")

    payment_id = int(payment_id_str)
    room_id = int(room_id_str)

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
        # ПРОВЕРКА УЧАСТИЯ
        # --------------------------------

        permission = await PaymentPermissionService.can_manage(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if permission == PaymentPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПОЛУЧАЕМ ПЛАТЁЖ ДО УДАЛЕНИЯ
        # --------------------------------

        payment = await RoomPaymentService.get_payment(
            session=session,
            payment_id=payment_id,
        )

        if payment is None:
            await callback.answer(
                "❌ Платёж уже удалён.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПРОВЕРКА КОМНАТЫ
        # --------------------------------

        if payment.room_id != room_id:
            await callback.answer(
                "❌ Платёж относится к другой комнате.",
                show_alert=True,
            )
            return

        # --------------------------------
        # СОХРАНЯЕМ ДАННЫЕ ПЛАТЕЖА
        # ДО УДАЛЕНИЯ
        # --------------------------------

        payment_description = (
            payment.description
            if payment.description
            else "Расход"
        )

        payment_amount = payment.amount

        # --------------------------------
        # ПОЛУЧАЕМ УЧАСТНИКОВ
        # ДО УДАЛЕНИЯ
        # --------------------------------

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        # --------------------------------
        # УДАЛЯЕМ ПЛАТЁЖ
        # --------------------------------

        deleted = await RoomPaymentService.delete_payment(
            session=session,
            payment_id=payment_id,
        )

        if not deleted:
            await callback.answer(
                "❌ Не удалось удалить платёж.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ЗАПИСЫВАЕМ В ИСТОРИЮ
        # --------------------------------

        await RoomHistoryService.create(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            action="payment_deleted",
            description=payment_description,
            amount=payment_amount,
        )

        # --------------------------------
        # ПОЛУЧАЕМ ОБНОВЛЁННЫЕ ПЛАТЕЖИ
        # --------------------------------

        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        # --------------------------------
        # ПЕРЕСЧИТЫВАЕМ ДОЛГИ
        # --------------------------------

        details = DebtService.calculate_details(
            members=members,
            payments=payments,
        )

        balances = details["balances"]
        share = details["share"]

        # --------------------------------
        # КТО УДАЛИЛ ПЛАТЁЖ
        # --------------------------------

        deleted_by_name = (
            current_user.first_name
            or current_user.username
            or "Пользователь"
        )

        # --------------------------------
        # ПЕРСОНАЛЬНЫЕ УВЕДОМЛЕНИЯ
        # --------------------------------

        for member in members:

            user = await UserRepository.get_by_id(
                session=session,
                user_id=member.user_id,
            )

            if user is None:
                continue

            balance = balances.get(
                user.id,
                0,
            )

            await NotificationService.notify_debt_changed_after_delete(
                bot=bot,
                session=session,
                room_id=room_id,
                telegram_id=user.telegram_id,
                user_name=deleted_by_name,
                description=payment_description,
                amount=float(payment_amount),
                share=float(share),
                balance=float(balance),
            )

        await session.commit()

    # --------------------------------
    # ФОРМИРУЕМ ОБНОВЛЁННЫЙ СПИСОК
    # --------------------------------

    async with AsyncSessionLocal() as session:

        split = await SplitBillService.calculate(
            session=session,
            room_id=room_id,
        )

        text = _payments_text(payments, split)

        await AnchorService.render(
            bot=bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=payment_manage_menu(
                room_id=room_id,
                payments=payments,
            ),
        )

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

        room_total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        async def render_menu_for(member_user_id):
            return build_menu_screen(
                room=room,
                total=room_total,
                members=members,
                is_owner=(member_user_id == room.owner_id),
            )

        for member in members:

            if member.user_id == current_user.id:
                continue

            text_for_member, keyboard_for_member = await render_menu_for(
                member.user_id
            )

            await AnchorService.render(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=member.user_id,
                text=text_for_member,
                keyboard=keyboard_for_member,
            )

        await session.commit()

    await callback.answer(
        "✅ Платёж удалён"
    )

@router.callback_query(
    F.data.startswith("payment_manage:")
)
async def payment_manage(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

        # Текущий пользователь
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

        permission = await PaymentPermissionService.can_manage(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if permission == PaymentPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        # Получаем платежи
        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        split = await SplitBillService.calculate(
            session=session,
            room_id=room_id,
        )

        text = _payments_text(payments, split)

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=payment_manage_menu(
                room_id=room_id,
                payments=payments,
            ),
        )

        await session.commit()

    await callback.answer()


@router.callback_query(
    F.data.startswith("payment_add:")
)
async def payment_add(
    callback: CallbackQuery,
    state: FSMContext,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

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

        permission = await PaymentPermissionService.can_manage(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if permission == PaymentPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

    builder = InlineKeyboardBuilder()

    for member in members:
        name = (
            member.user.first_name
            if member.user
            else "Неизвестный"
        )

        builder.button(
            text=f"💳 {name}",
            callback_data=(
                f"payment_payer:{room_id}:{member.user_id}"
            ),
        )

    builder.button(
        text="⬅️ Назад",
        callback_data=f"payment_manage:{room_id}",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        "💳 <b>Кто оплатил?</b>\n\n"
        "Выберите участника, который внёс деньги:",
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("payment_payer:")
)
async def payment_payer(
    callback: CallbackQuery,
    state: FSMContext,
):
    _, room_id_str, user_id_str = callback.data.split(":")

    room_id = int(room_id_str)
    user_id = int(user_id_str)

    async with AsyncSessionLocal() as session:

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

        permission = await PaymentPermissionService.can_manage(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if permission == PaymentPermission.NOT_MEMBER:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        payer = await UserRepository.get_by_id(
            session=session,
            user_id=user_id,
        )

        if payer is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        await state.set_state(
            PaymentState.waiting_amount
        )

        await state.update_data(
            room_id=room_id,
            payer_id=user_id,
        )

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=(
                f"💳 Плательщик: <b>{payer.first_name}</b>\n\n"
                "💰 Введите сумму платежа:"
            ),
        )

        await session.commit()

    await callback.answer()


@router.message(PaymentState.waiting_amount)
async def payment_amount(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    room_id = data.get("room_id")
    payer_id = data.get("payer_id")

    if not room_id or not payer_id:
        await state.clear()

        await message.answer(
            "❌ Сессия добавления платежа устарела."
        )
        return

    try:
        amount = float(
            message.text.replace(",", ".")
        )
    except (ValueError, AttributeError):
        await message.answer(
            "❌ Введите корректную сумму.\n\n"
            "Например:\n"
            "100"
        )
        return

    if amount <= 0:
        await message.answer(
            "❌ Сумма должна быть больше 0."
        )
        return

    await state.update_data(
        amount=amount,
    )

    async with AsyncSessionLocal() as session:

        user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=message.from_user.id,
        )

        if user is not None:
            await AnchorService.render(
                bot=message.bot,
                session=session,
                room_id=room_id,
                user_id=user.id,
                text=(
                    f"💰 Сумма: <b>{amount:.2f} zł</b>\n\n"
                    "📝 Введите название расхода.\n\n"
                    "Например:\n"
                    "Пицца"
                ),
            )

        await session.commit()

    try:
        await message.delete()
    except Exception:
        pass

    await state.set_state(
        PaymentState.waiting_description
    )

@router.message(PaymentState.waiting_description)
async def payment_description(
    message: Message,
    state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()

    room_id = data.get("room_id")
    payer_id = data.get("payer_id")
    amount = data.get("amount")

    # --------------------------------
    # ПРОВЕРКА СЕССИИ
    # --------------------------------

    if not room_id or not payer_id or amount is None:
        await state.clear()

        await message.answer(
            "❌ Сессия добавления платежа устарела."
        )
        return

    # --------------------------------
    # ПРОВЕРКА ТЕКСТА
    # --------------------------------

    if not message.text:
        await message.answer(
            "❌ Введите название расхода."
        )
        return

    description = message.text.strip()

    if not description:
        await message.answer(
            "❌ Введите название расхода.\n\n"
            "Например: Пицца"
        )
        return

    async with AsyncSessionLocal() as session:

        # --------------------------------
        # ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
        # --------------------------------

        current_user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=message.from_user.id,
        )

        if current_user is None:
            await state.clear()

            await message.answer(
                "❌ Пользователь не найден."
            )
            return

        # --------------------------------
        # ПРОВЕРЯЕМ ПЛАТЕЛЬЩИКА
        # --------------------------------

        payer_is_member = await RoomMemberService.is_member(
            session=session,
            room_id=room_id,
            user_id=payer_id,
        )

        if not payer_is_member:
            await state.clear()

            await message.answer(
                "❌ Этот пользователь больше не является "
                "участником комнаты."
            )
            return

        # --------------------------------
        # СОЗДАЁМ ПЛАТЁЖ
        # --------------------------------

        await RoomPaymentService.create_payment(
            session=session,
            room_id=room_id,
            user_id=payer_id,
            amount=amount,
            description=description,
        )

        # --------------------------------
        # ПОЛУЧАЕМ УЧАСТНИКОВ
        # --------------------------------

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        # --------------------------------
        # ПОЛУЧАЕМ ПЛАТЕЛЬЩИКА
        # --------------------------------

        payer = await UserRepository.get_by_id(
            session=session,
            user_id=payer_id,
        )

        payer_name = (
            payer.first_name
            if payer
            else "Пользователь"
        )

        # --------------------------------
        # ЗАПИСЫВАЕМ В ИСТОРИЮ
        # --------------------------------

        await RoomHistoryService.create(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            action="payment_added",
            description=description,
            amount=amount,
        )

        # --------------------------------
        # ПОЛУЧАЕМ ОБНОВЛЁННЫЕ ПЛАТЕЖИ
        # --------------------------------

        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        # --------------------------------
        # РАССЧИТЫВАЕМ ДОЛГИ
        # --------------------------------

        details = DebtService.calculate_details(
            members=members,
            payments=payments,
        )

        balances = details["balances"]
        share = details["share"]

        # --------------------------------
        # ПЕРСОНАЛЬНЫЕ УВЕДОМЛЕНИЯ
        # --------------------------------

        for member in members:

            user = await UserRepository.get_by_id(
                session=session,
                user_id=member.user_id,
            )

            if user is None:
                continue

            balance = balances.get(
                user.id,
                0,
            )

            await NotificationService.notify_debt_changed(
                bot=bot,
                session=session,
                room_id=room_id,
                telegram_id=user.telegram_id,
                payer_name=payer_name,
                description=description,
                amount=amount,
                share=float(share),
                balance=float(balance),
            )

        # --------------------------------
        # ФОРМИРУЕМ ФИНАЛЬНОЕ СООБЩЕНИЕ
        # --------------------------------

        split = await SplitBillService.calculate(
            session=session,
            room_id=room_id,
        )

        text = (
            "✅ <b>Платёж добавлен</b>\n\n"
            + _payments_text(payments, split)
        )

        await AnchorService.render(
            bot=bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=payment_manage_menu(
                room_id=room_id,
                payments=payments,
            ),
        )

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        if room is None:
            await message.answer(
                "❌ Комната не найдена."
            )
            await state.clear()
            return

        room_total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        for member in members:

            if member.user_id == current_user.id:
                continue

            menu_text, menu_keyboard = build_menu_screen(
                room=room,
                total=room_total,
                members=members,
                is_owner=(member.user_id == room.owner_id),
            )

            await AnchorService.render(
                bot=bot,
                session=session,
                room_id=room_id,
                user_id=member.user_id,
                text=menu_text,
                keyboard=menu_keyboard,
            )

        await session.commit()

    await state.clear()

    try:
        await message.delete()
    except Exception:
        pass
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.debt_result_menu import debt_result_menu
from keyboards.payment_delete_menu import payment_delete_menu
from services.room_member_service import RoomMemberService
from services.room_history_service import RoomHistoryService


from database.session import AsyncSessionLocal
from database.models import RoomPayment

from services.room_access_service import RoomAccessService
from services.split_bill_service import SplitBillService
from services.room_payment_service import RoomPaymentService

from repositories.user_repository import UserRepository

from states.payment_state import PaymentState
from services.debt_service import DebtService

from keyboards.payment_menu import payment_menu
from keyboards.payment_manage_menu import payment_manage_menu


router = Router()


@router.callback_query(
    F.data.startswith("payment_user:")
)
async def payment_user(
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

        has_access = await RoomAccessService.check_access(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        print(
            "PAYMENT DELETE ACCESS:",
            "room_id =", room_id,
            "user_id =", current_user.id,
            "has_access =", has_access,
        )

        if not has_access:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        data = await SplitBillService.calculate(
            session=session,
            room_id=room_id,
        )

        member = next(
            (
                member
                for member in data["members"]
                if member.user_id == user_id
            ),
            None,
        )

        if member is None:
            await callback.answer(
                "❌ Этот пользователь не является участником комнаты.",
                show_alert=True,
            )
            return

        payer_name = (
            member.user.first_name
            if member.user
            else "Неизвестный"
        )

    await state.update_data(
        room_id=room_id,
        payer_id=user_id,
        payer_name=payer_name,
    )

    await state.set_state(
        PaymentState.waiting_amount
    )

    await callback.message.answer(
        f"""
💳 <b>Плательщик:</b> {payer_name}

Введите сумму, которую он оплатил.

Например:
<code>100</code>
""",
        parse_mode="HTML",
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("payment_done:")
)

async def payment_done(
    callback: CallbackQuery,
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

        data = await SplitBillService.calculate(
            session=session,
            room_id=room_id,
        )

        members = data["members"]
        total = data["total"]

        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        if not payments:
            await callback.answer(
                "❌ Добавьте хотя бы одного плательщика.",
                show_alert=True,
            )
            return

        paid_total = sum(
            payment.amount
            for payment in payments
        )

        remaining = total - paid_total

        if remaining > 0.01:
            await callback.answer(
                f"⚠️ Осталось распределить "
                f"{remaining:.2f} zł.",
                show_alert=True,
            )
            return

        transfers = DebtService.calculate(
            members=members,
            payments=payments,
        )

        users = {
            member.user_id: (
                member.user.first_name
                if member.user
                else "Неизвестный"
            )
            for member in members
        }

    # --------------------------------
    # РАСХОДЫ
    # --------------------------------

    payments_text = ""

    for payment in payments:

        payer_name = users.get(
            payment.user_id,
            "Неизвестный",
        )

        description = (
            payment.description
            if payment.description
            else "Расход"
        )

        payments_text += (
            f"• {description}: "
            f"<b>{payment.amount:.2f} zł</b>\n"
            f"  💳 {payer_name}\n"
        )

    # --------------------------------
    # ИТОГОВЫЕ ПЛАТЕЖИ
    # --------------------------------

    debts_text = ""

    if transfers:

        for transfer in transfers:

            from_name = users.get(
                transfer["from_user_id"],
                "Неизвестный",
            )

            to_name = users.get(
                transfer["to_user_id"],
                "Неизвестный",
            )

            debts_text += (
                f"• <b>{from_name}</b> → "
                f"<b>{to_name}</b>: "
                f"<b>{transfer['amount']:.2f} zł</b>\n"
            )

    else:

        debts_text = (
            "🎉 Никому ничего переводить не нужно.\n"
        )

    text = (
        "🧮 <b>Итоговый расчёт</b>\n\n"

        "🧾 <b>Расходы</b>\n\n"
        f"{payments_text}\n"

        "────────────────\n\n"

        f"💰 <b>Общая сумма:</b> "
        f"{total:.2f} zł\n"

        f"👥 <b>Участников:</b> "
        f"{len(members)}\n\n"

        "💸 <b>Кто кому должен</b>\n\n"
        f"{debts_text}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=debt_result_menu(
            room_id=room_id,
        ),
    )

    await callback.answer(
        "✅ Расчёт завершён."
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

        # Проверяем именно членство в комнате
        is_member = await RoomMemberService.is_member(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not is_member:
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

    await callback.message.edit_text(
        (
            "🗑 <b>Удалить платёж?</b>\n\n"
            f"💳 Плательщик: <b>{payer_name}</b>\n"
            f"💰 Сумма: <b>{amount:.2f} zł</b>\n"
            f"📝 Расход: <b>{description}</b>\n\n"
            "Вы уверены?"
        ),
        parse_mode="HTML",
        reply_markup=payment_delete_menu(
            payment_id=payment_id,
            room_id=room_id,
        ),
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("payment_delete_confirm:")
)
async def payment_delete_confirm(
    callback: CallbackQuery,
):
    _, payment_id_str, room_id_str = callback.data.split(":")

    payment_id = int(payment_id_str)
    room_id = int(room_id_str)

    async with AsyncSessionLocal() as session:

        # Получаем текущего пользователя
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

        # Проверяем, что пользователь является участником комнаты
        is_member = await RoomMemberService.is_member(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not is_member:
            await callback.answer(
                "❌ Вы больше не участник этой комнаты.",
                show_alert=True,
            )
            return

        # Получаем платёж ДО удаления
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

        # Проверяем, что платёж относится именно к этой комнате
        if payment.room_id != room_id:
            await callback.answer(
                "❌ Платёж относится к другой комнате.",
                show_alert=True,
            )
            return

        # Сохраняем данные до удаления
        payment_description = (
            payment.description
            if payment.description
            else "Расход"
        )

        payment_amount = payment.amount

        # Удаляем платёж
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

        # Записываем удаление в историю
        await RoomHistoryService.create(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            action="payment_deleted",
            description=payment_description,
            amount=payment_amount,
        )

        # Получаем платежи ИМЕННО этой комнаты
        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

    # Формируем обновлённый список
    if not payments:

        text = (
            "💳 <b>Платежи комнаты</b>\n\n"
            "Пока нет добавленных платежей."
        )

    else:

        payments_text = ""
        total = 0

        for payment in payments:

            name = (
                payment.user.first_name
                if payment.user
                else "Неизвестный"
            )

            description = (
                payment.description
                if payment.description
                else "Расход"
            )

            total += payment.amount

            payments_text += (
                f"• <b>{name}</b> — "
                f"<b>{payment.amount:.2f} zł</b>\n"
                f"  📝 {description}\n\n"
            )

        text = (
            "💳 <b>Платежи комнаты</b>\n\n"
            f"{payments_text}"
            "────────────────\n"
            f"💰 Всего: <b>{total:.2f} zł</b>"
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=payment_manage_menu(
            room_id=room_id,
            payments=payments,
        ),
    )

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

        # Проверяем доступ к комнате
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

        # Получаем платежи
        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

    # Если платежей нет
    if not payments:
        text = (
            "💳 <b>Платежи комнаты</b>\n\n"
            "Пока нет добавленных платежей."
        )

    else:
        payments_text = ""

        total = 0

        for payment in payments:

            name = (
                payment.user.first_name
                if payment.user
                else "Неизвестный"
            )

            description = (
                payment.description
                if payment.description
                else "Расход"
            )

            total += payment.amount

            payments_text += (
                f"• <b>{name}</b> — "
                f"<b>{payment.amount:.2f} zł</b>\n"
                f"  📝 {description}\n\n"
            )

        text = (
            "💳 <b>Платежи комнаты</b>\n\n"
            f"{payments_text}"
            "────────────────\n"
            f"💰 Всего: <b>{total:.2f} zł</b>"
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=payment_manage_menu(
            room_id=room_id,
            payments=payments,
        ),
    )

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

        is_member = await RoomMemberService.is_member(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not is_member:
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

        is_member = await RoomMemberService.is_member(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not is_member:
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

    await callback.message.edit_text(
        f"💳 Плательщик: <b>{payer.first_name}</b>\n\n"
        "💰 Введите сумму платежа:",
        parse_mode="HTML",
    )

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

    await message.answer(
        f"💰 Сумма: <b>{amount:.2f} zł</b>\n\n"
        "📝 Введите название расхода.\n\n"
        "Например:\n"
        "Пицца",
        parse_mode="HTML",
    )

    await state.set_state(
        PaymentState.waiting_description
    )

@router.message(PaymentState.waiting_description)
async def payment_description(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    room_id = data.get("room_id")
    payer_id = data.get("payer_id")
    amount = data.get("amount")

    if not room_id or not payer_id or amount is None:
        await state.clear()

        await message.answer(
            "❌ Сессия добавления платежа устарела."
        )
        return

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

        # Получаем пользователя, который добавляет платёж
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

        # Проверяем, что плательщик всё ещё участник комнаты
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

        # Создаём платёж
        await RoomPaymentService.create_payment(
            session=session,
            room_id=room_id,
            user_id=payer_id,
            amount=amount,
            description=description,
        )

        # Записываем событие в историю
        await RoomHistoryService.create(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            action="payment_added",
            description=description,
            amount=amount,
        )

        # Получаем обновлённые платежи
        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

    await state.clear()

    payments_text = ""
    total = 0

    for payment in payments:

        name = (
            payment.user.first_name
            if payment.user
            else "Неизвестный"
        )

        payment_description = (
            payment.description
            if payment.description
            else "Расход"
        )

        total += payment.amount

        payments_text += (
            f"• <b>{name}</b> — "
            f"<b>{payment.amount:.2f} zł</b>\n"
            f"  📝 {payment_description}\n\n"
        )

    text = (
        "✅ <b>Платёж добавлен</b>\n\n"
        "💳 <b>Платежи комнаты</b>\n\n"
        f"{payments_text}"
        "────────────────\n"
        f"💰 Всего: <b>{total:.2f} zł</b>"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=payment_manage_menu(
            room_id=room_id,
            payments=payments,
        ),
    )
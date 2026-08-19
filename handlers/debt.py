from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.debt_optimize_menu import debt_optimize_menu

from database.session import AsyncSessionLocal

from repositories.user_repository import UserRepository

from services.room_access_service import RoomAccessService
from services.room_member_service import RoomMemberService
from services.room_payment_service import RoomPaymentService
from services.debt_service import DebtService
from services.settlement_service import SettlementService

from keyboards.debt_menu import debt_menu


router = Router()


@router.callback_query(
    F.data.startswith("debt_calculate:")
)
async def debt_calculate(
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

        # Получаем участников
        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        # Получаем платежи
        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        # Получаем подтверждённые погашения
        settlements = await SettlementService.get_confirmed_for_room(
            session=session,
            room_id=room_id,
        )

        # Полный расчёт с учётом погашений
        details = DebtService.calculate_details(
            members=members,
            payments=payments,
            settlements=settlements,
        )

        # Получаем пользователей
        users = {}

        for member in members:

            user = await UserRepository.get_by_id(
                session=session,
                user_id=member.user_id,
            )

            if user:
                users[user.id] = user

    total = details["total"]
    share = details["share"]
    balances = details["balances"]
    transfers = details["transfers"]

    # Если платежей нет
    if total <= 0:

        text = (
            "💸 <b>Расчёт долгов</b>\n\n"
            "💰 Общие расходы: <b>0.00 zł</b>\n"
            f"👥 Участников: <b>{len(members)}</b>\n\n"
            "📊 Пока нет платежей."
        )

    else:

        # Балансы
        balances_text = ""

        for user_id, balance in balances.items():

            user = users.get(user_id)

            name = (
                user.first_name
                if user
                else "Неизвестный"
            )

            if balance > 0:
                icon = "🟢"
                sign = "+"
            elif balance < 0:
                icon = "🔴"
                sign = ""
            else:
                icon = "⚪"
                sign = ""

            balances_text += (
                f"{icon} <b>{name}</b>\n"
                f"{sign}{balance:.2f} zł\n\n"
            )

        # Переводы
        transfers_text = ""

        for transfer in transfers:

            from_user = users.get(
                transfer["from_user_id"]
            )

            to_user = users.get(
                transfer["to_user_id"]
            )

            from_name = (
                from_user.first_name
                if from_user
                else "Неизвестный"
            )

            to_name = (
                to_user.first_name
                if to_user
                else "Неизвестный"
            )

            amount = transfer["amount"]

            transfers_text += (
                f"🔴 <b>{from_name}</b> → "
                f"🟢 <b>{to_name}</b>\n"
                f"💰 <b>{amount:.2f} zł</b>\n\n"
            )

        # Основной текст
        text = (
            "💸 <b>РАСЧЁТ ДОЛГОВ</b>\n\n"

            f"💰 Общие расходы: "
            f"<b>{total:.2f} zł</b>\n"

            f"👥 Участников: "
            f"<b>{len(members)}</b>\n"

            f"💵 Средняя доля: "
            f"<b>{share:.2f} zł</b>\n\n"

            "📊 <b>БАЛАНСЫ</b>\n\n"
            f"{balances_text}"

            "────────────────\n\n"

            "💸 <b>КТО КОМУ ДОЛЖЕН</b>\n\n"
        )

        if transfers_text:
            text += transfers_text
        else:
            text += (
                "✅ <b>Все рассчитались.</b>\n"
            )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=debt_menu(
            room_id=room_id,
        ),
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("debt_optimize:")
)
async def debt_optimize(
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

        # Получаем участников
        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        # Получаем платежи
        payments = await RoomPaymentService.get_room_payments(
            session=session,
            room_id=room_id,
        )

        # Получаем подтверждённые погашения
        settlements = await SettlementService.get_confirmed_for_room(
            session=session,
            room_id=room_id,
        )

        # Рассчитываем долги с учётом погашений
        transfers = DebtService.calculate(
            members=members,
            payments=payments,
            settlements=settlements,
        )

        # Получаем пользователей
        users = {}

        for member in members:

            user = await UserRepository.get_by_id(
                session=session,
                user_id=member.user_id,
            )

            if user:
                users[user.id] = user

    if not transfers:

        text = (
            "⚡ <b>ОПТИМИЗАЦИЯ ДОЛГОВ</b>\n\n"
            "✅ Все долги уже закрыты.\n\n"
            "Ни одному участнику не нужно "
            "переводить деньги."
        )

    else:

        transfers_text = ""
        total_transfers = 0
        total_amount = 0

        for transfer in transfers:

            from_user = users.get(
                transfer["from_user_id"]
            )

            to_user = users.get(
                transfer["to_user_id"]
            )

            from_name = (
                from_user.first_name
                if from_user
                else "Неизвестный"
            )

            to_name = (
                to_user.first_name
                if to_user
                else "Неизвестный"
            )

            amount = transfer["amount"]

            total_transfers += 1
            total_amount += amount

            transfers_text += (
                f"🔴 <b>{from_name}</b> → "
                f"🟢 <b>{to_name}</b>\n"
                f"💰 <b>{amount:.2f} zł</b>\n\n"
            )

        text = (
            "⚡ <b>ОПТИМИЗАЦИЯ ДОЛГОВ</b>\n\n"
            "Чтобы закрыть все долги:\n\n"
            f"{transfers_text}"
            "────────────────\n\n"
            f"📌 Переводов: <b>{total_transfers}</b>\n"
            f"💰 Всего: <b>{total_amount:.2f} zł</b>"
        )

    await callback.message.edit_text(
    text,
    parse_mode="HTML",
    reply_markup=debt_optimize_menu(
        room_id=room_id,
        transfers=transfers,
    ),

    )

    await callback.answer()
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from keyboards.payment_menu import payment_menu

from services.split_bill_service import SplitBillService
from services.room_access_service import RoomAccessService

from repositories.user_repository import UserRepository


router = Router()


@router.callback_query(F.data.startswith("room_split:"))
async def split_bill(
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

    await callback.message.edit_text(
        f"""
💸 <b>Разделение счета</b>

💰 Общая сумма:
<b>{data['total']:.2f} zł</b>

👥 Участников:
<b>{data['count']}</b>

💰 На человека:
<b>{data['per_person']:.2f} zł</b>

────────────────

💳 <b>Кто оплатил счёт?</b>
""",
        parse_mode="HTML",
        reply_markup=payment_menu(
            room_id=room_id,
            members=data["members"],
        ),
    )

    await callback.answer()
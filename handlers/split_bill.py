from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

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

    members_text = ""

    for member in data["members"]:

        name = member.user.first_name

        members_text += (
            f"• {name}: "
            f"<b>{data['per_person']:.2f} zł</b>\n"
        )

    await callback.message.answer(
        f"""
💸 <b>Разделение счета</b>

💰 Общая сумма:
<b>{data['total']:.2f} zł</b>

👥 Участников:
<b>{data['count']}</b>

────────────────

{members_text}
""",
        parse_mode="HTML",
    )

    await callback.answer()
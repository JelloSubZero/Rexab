from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from services.split_bill_service import SplitBillService

router = Router()


@router.callback_query(F.data.startswith("room_split:"))
async def split_bill(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

    async with AsyncSessionLocal() as session:

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
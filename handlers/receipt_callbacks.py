from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from database.session import AsyncSessionLocal

from services.room_service import RoomService
from services.qr_service import QRService

from states.receipt_state import ReceiptState

from keyboards.room_menu import room_menu

from services.room_view_service import RoomViewService

from repositories.user_repository import UserRepository
router = Router()




@router.callback_query(F.data.startswith("add_receipt:"))
async def add_receipt(
    callback: CallbackQuery,
    state: FSMContext,
):
    room_id = int(callback.data.split(":")[1])

    await state.update_data(
        room_id=room_id,
    )

    await state.set_state(
        ReceiptState.waiting_receipt,
    )

    await callback.message.answer(
        "📷 Отправьте следующий чек."
    )

    await callback.answer()


@router.callback_query(F.data.startswith("finish_receipts:"))
async def finish_receipts(
    callback: CallbackQuery,
    state: FSMContext,
):
    room_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:

        room_data = await RoomViewService.build(
            session=session,
            room_id=room_id,
        )

    room = room_data["room"]
    total = room_data["total"] or 0
    members = room_data["members"]

    members_text = ""

    for index, member in enumerate(members, start=1):

        name = member.user.first_name

        if member.user_id == room.owner_id:
            name += " 👑"

        members_text += f"{index}. {name}\n"

    msg = await callback.message.answer(
        f"""
🏠 <b>Комната</b>

🔑 Код:
<code>{room.code}</code>

💰 Общая сумма:
<b>{total:.2f} zł</b>

👥 Участников: {len(members)}

{members_text}
""",
        parse_mode="HTML",
        reply_markup=room_menu(room.id),
    )

    # Сохраняем экран комнаты владельца
    async with AsyncSessionLocal() as session:

        owner = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=callback.from_user.id,
        )

        await RoomViewService.save_message(
            session=session,
            room_id=room.id,
            user_id=owner.id,
            chat_id=callback.message.chat.id,
            message_id=msg.message_id,
        )

    await state.clear()

    await callback.answer()
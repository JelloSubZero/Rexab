from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from services.room_member_service import RoomMemberService

from database.session import AsyncSessionLocal
from repositories.user_repository import UserRepository
from services.room_service import RoomService

from states.receipt_state import ReceiptState

router = Router()


@router.message(F.text == "➕ Создать чек")
async def create_room(
    message: Message,
    state: FSMContext,
):
    async with AsyncSessionLocal() as session:

        user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=message.from_user.id,
        )

        if user is None:
            await message.answer(
                "❌ Пользователь не найден. Выполните команду /start."
            )
            return

        room = await RoomService.create_room(
            session=session,
            owner_id=user.id,
        )
        await RoomMemberService.join_room(
        session=session,
        room_id=room.id,
        user_id=user.id,
    )
    # Сохраняем ID комнаты в FSM
    await state.update_data(room_id=room.id)

    # Ожидаем загрузку фотографии чека
    await state.set_state(ReceiptState.waiting_receipt)

    await message.answer(
    f"""
🏠 <b>Комната создана</b>

🔑 Код комнаты:
<code>{room.code}</code>

📸 Отправьте первый чек.

После загрузки чеков вы сможете пригласить участников.
""",
    parse_mode="HTML",
)
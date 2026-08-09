from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from services.room_member_service import RoomMemberService

from database.session import AsyncSessionLocal
from repositories.user_repository import UserRepository
from services.room_service import RoomService
from services.room_view_service import RoomViewService

from keyboards.room_menu import room_menu
from services.room_access_service import RoomAccessService

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


@router.callback_query(
    F.data.startswith("room_back:")
)
async def room_back(
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

        room_data = await RoomViewService.build(
            session=session,
            room_id=room_id,
        )

        room = room_data["room"]
        total = room_data["total"] or 0
        members = room_data["members"]

        members_text = ""

        for index, member in enumerate(
            members,
            start=1,
        ):
            name = (
                member.user.first_name
                if member.user
                else "Неизвестный"
            )

            if member.user_id == room.owner_id:
                name += " 👑"

            members_text += (
                f"{index}. {name}\n"
            )

    text = (
        "🏠 <b>Комната</b>\n\n"
        f"🔑 Код:\n"
        f"<code>{room.code}</code>\n\n"
        f"💰 Общая сумма:\n"
        f"<b>{total:.2f} zł</b>\n\n"
        f"👥 Участников: {len(members)}\n\n"
        f"{members_text}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=room_menu(
            room.id,
        ),
    )

    await callback.answer()
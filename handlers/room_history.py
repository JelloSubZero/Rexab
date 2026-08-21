from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal
from repositories.user_repository import UserRepository
from services.room_access_service import RoomAccessService
from services.room_history_service import RoomHistoryService
from services.anchor_service import AnchorService
from keyboards.room_history_menu import room_history_menu


router = Router()


@router.callback_query(
    F.data.startswith("room_history:")
)
async def room_history(
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

        # Получаем историю
        history = await RoomHistoryService.get_room_history(
            session=session,
            room_id=room_id,
        )

        if not history:
            text = (
                "📜 <b>История комнаты</b>\n\n"
                "История пока пуста."
            )

        else:

            history_text = ""

            for item in history:

                if item.action == "payment_added":
                    icon = "➕"
                    action_text = "добавил платёж"

                elif item.action == "payment_deleted":
                    icon = "🗑"
                    action_text = "удалил платёж"

                elif item.action == "member_joined":
                    icon = "👤"
                    action_text = "присоединился к комнате"

                else:
                    icon = "ℹ️"
                    action_text = item.action

                user_name = (
                    item.user.first_name
                    if item.user
                    else "Неизвестный"
                )

                history_text += (
                    f"{icon} <b>{user_name}</b> "
                    f"{action_text}\n"
                )

                if item.description and item.action not in (
                    "member_joined",
                ):
                    history_text += (
                        f"📝 {item.description}\n"
                    )

                if item.amount is not None:
                    history_text += (
                        f"💰 {item.amount:.2f} zł\n"
                    )

                history_text += "\n"

            text = (
                "📜 <b>История комнаты</b>\n\n"
                f"{history_text}"
            )

        await AnchorService.render(
            bot=callback.bot,
            session=session,
            room_id=room_id,
            user_id=current_user.id,
            text=text,
            keyboard=room_history_menu(
                room_id=room_id,
            ),
        )

        await session.commit()

    await callback.answer()
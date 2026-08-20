import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from services.room_member_service import RoomMemberService
from database.models import RoomStatus
from keyboards.room_close_confirm_menu import room_close_confirm_menu
from aiogram.exceptions import TelegramBadRequest
from services.room_message_service import RoomMessageService

from database.session import AsyncSessionLocal
from repositories.user_repository import UserRepository
from services.room_service import RoomService
from services.room_view_service import RoomViewService

from keyboards.room_menu import room_menu
from services.room_access_service import RoomAccessService
from services.room_permission_service import RoomPermissionService

from states.receipt_state import ReceiptState

logger = logging.getLogger(__name__)

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

        await state.update_data(
            room_id=room.id,
        )

        await state.set_state(
            ReceiptState.waiting_receipt,
        )

        sent_message = await message.answer(
            f"""
    🏠 <b>Комната создана</b>

    🔑 Код комнаты:
    <code>{room.code}</code>

    📸 Отправьте первый чек.

    После загрузки чеков вы сможете пригласить участников.
    """,
            parse_mode="HTML",
        )

        await RoomMessageService.save(
            session=session,
            room_id=room.id,
            chat_id=sent_message.chat.id,
            message_id=sent_message.message_id,
        )

        await session.commit()

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
        f"🏠 <b>{room.name or 'Комната'}</b>\n\n"
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
        is_owner=(room.owner_id == current_user.id),
    ),
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("room_close:")
)
async def room_close(
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

        is_owner = await RoomPermissionService.is_owner(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not is_owner:
            await callback.answer(
                "❌ Только владелец может закрыть комнату.",
                show_alert=True,
            )
            return

    await callback.message.edit_text(
        "🔒 <b>Закрытие комнаты</b>\n\n"
        "Вы уверены, что хотите закрыть комнату?\n\n"
        "После закрытия новые участники "
        "не смогут присоединиться.",
        parse_mode="HTML",
        reply_markup=room_close_confirm_menu(
            room_id=room_id,
        ),
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("room_close_confirm:")
)
async def room_close_confirm(
    callback: CallbackQuery,
):
    room_id = int(
        callback.data.split(":")[1]
    )

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
        # КОМНАТА
        # --------------------------------

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

        # --------------------------------
        # ТОЛЬКО ВЛАДЕЛЕЦ
        # --------------------------------

        is_owner = await RoomPermissionService.is_owner(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if not is_owner:
            await callback.answer(
                "❌ Только владелец может закрыть комнату.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПРОВЕРКА СТАТУСА
        # --------------------------------

        if room.status != RoomStatus.ACTIVE.value:
            await callback.answer(
                "❌ Комната уже закрыта.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ЗАКРЫВАЕМ
        # --------------------------------

        room.status = RoomStatus.CLOSED.value

        await session.commit()

        # --------------------------------
        # ЧИСТИМ НАКОПИВШИЕСЯ СООБЩЕНИЯ
        # --------------------------------

        await RoomMessageService.delete_all(
            bot=callback.bot,
            session=session,
            room_id=room_id,
        )

        await session.commit()

        # --------------------------------
        # ЭКРАН ВЛАДЕЛЬЦА
        # --------------------------------

        owner_view = await RoomViewService.render_closed(
            session=session,
            room_id=room_id,
            user_id=current_user.id,
        )

        if owner_view is not None:

            await callback.message.edit_text(
                owner_view["text"],
                parse_mode="HTML",
                reply_markup=owner_view["reply_markup"],
            )

            # Обновляем RoomView владельца
            # на актуальное сообщение
            await RoomViewService.save_message(
                session=session,
                room_id=room_id,
                user_id=current_user.id,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
            )

        # --------------------------------
        # ОСТАЛЬНЫЕ УЧАСТНИКИ
        # --------------------------------

        room_views = await RoomViewService.get_views(
            session=session,
            room_id=room_id,
        )

        for room_view in room_views:

            # Владельца уже обновили выше
            if room_view.user_id == current_user.id:
                continue

            view = await RoomViewService.render_closed(
                session=session,
                room_id=room_id,
                user_id=room_view.user_id,
            )

            if view is None:
                continue

            try:

                await callback.bot.edit_message_text(
                    chat_id=room_view.chat_id,
                    message_id=room_view.message_id,
                    text=view["text"],
                    parse_mode="HTML",
                    reply_markup=view["reply_markup"],
                )

            except TelegramBadRequest:
                pass

            except Exception:
                logger.warning(
                    "Не удалось обновить закрытую комнату "
                    "для пользователя %s",
                    room_view.user_id,
                    exc_info=True,
                )

            await session.commit()
            
    await callback.answer(
        "✅ Комната закрыта"
    )
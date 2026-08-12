from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database.session import AsyncSessionLocal

from keyboards.room_members_menu import room_members_menu

from services.room_service import RoomService
from services.room_member_service import RoomMemberService
from services.room_access_service import RoomAccessService
from services.notification_service import NotificationService

from repositories.user_repository import UserRepository


router = Router()


@router.callback_query(F.data.startswith("room_members:"))
async def room_members(
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

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

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

    if not members_text:
        members_text = "Пока нет участников."

    text = (
        "👥 <b>Участники комнаты</b>\n\n"
        f"{members_text}\n"
        "───────────────\n"
        f"👥 Всего: <b>{len(members)}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=room_members_menu(
            room_id=room_id,
            members=members,
            owner_id=room.owner_id,
        ),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("remove_member:"))
async def remove_member(
    callback: CallbackQuery,
    bot: Bot,
):
    _, room_id_str, user_id_str = callback.data.split(":")

    room_id = int(room_id_str)
    user_id = int(user_id_str)

    async with AsyncSessionLocal() as session:

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

        if current_user.id != room.owner_id:
            await callback.answer(
                "❌ Только владелец комнаты может удалять участников.",
                show_alert=True,
            )
            return

        if user_id == room.owner_id:
            await callback.answer(
                "❌ Нельзя удалить владельца комнаты.",
                show_alert=True,
            )
            return

        # --------------------------------
        # ПОЛУЧАЕМ УДАЛЯЕМОГО ПОЛЬЗОВАТЕЛЯ
        # ДО УДАЛЕНИЯ
        # --------------------------------

        removed_user = await UserRepository.get_by_id(
            session=session,
            user_id=user_id,
        )

        if removed_user is None:
            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )
            return

        removed_user_name = (
            removed_user.first_name
            or removed_user.username
            or "Пользователь"
        )

        # --------------------------------
        # ПОЛУЧАЕМ УЧАСТНИКОВ
        # ДО УДАЛЕНИЯ
        # --------------------------------

        members_before = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        telegram_ids = []

        for member in members_before:

            # Самому удалённому уведомление не отправляем
            if member.user_id == user_id:
                continue

            member_user = await UserRepository.get_by_id(
                session=session,
                user_id=member.user_id,
            )

            if member_user:
                telegram_ids.append(
                    member_user.telegram_id
                )

        # --------------------------------
        # УДАЛЯЕМ УЧАСТНИКА
        # --------------------------------

        removed = await RoomMemberService.remove_member(
            session=session,
            room_id=room_id,
            user_id=user_id,
        )

        if not removed:
            await callback.answer(
                "❌ Участник не найден.",
                show_alert=True,
            )
            return

        # --------------------------------
        # УВЕДОМЛЕНИЕ
        # --------------------------------

        await NotificationService.notify_member_removed(
            bot=bot,
            session=session,
            room_id=room_id,
            telegram_ids=telegram_ids,
            member_name=removed_user_name,
        )

        # --------------------------------
        # ПОЛУЧАЕМ ОБНОВЛЁННЫЙ СПИСОК
        # --------------------------------

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

    # --------------------------------
    # ФОРМИРУЕМ СПИСОК
    # --------------------------------

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

    if not members_text:
        members_text = "Пока нет участников."

    text = (
        "👥 <b>Участники комнаты</b>\n\n"
        f"{members_text}\n"
        "───────────────\n"
        f"👥 Всего: <b>{len(members)}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=room_members_menu(
            room_id=room_id,
            members=members,
            owner_id=room.owner_id,
        ),
    )

    await callback.answer(
        "✅ Участник удален."
    )
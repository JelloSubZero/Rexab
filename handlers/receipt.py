import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from services.receipt_permission_service import (
    ReceiptPermission,
    ReceiptPermissionService,
)

from repositories.user_repository import UserRepository

from services.room_service import RoomService
from services.room_member_service import RoomMemberService
from services.anchor_service import AnchorService, build_menu_screen

from config import RECEIPTS_DIR

from database.session import AsyncSessionLocal

from services.receipt_service import ReceiptService
from services.ocr.ocr_service import OCRService

from states.receipt_state import ReceiptState

logger = logging.getLogger(__name__)

router = Router()


# ============================================================
# ЗАГРУЗКА ЧЕКА
# ============================================================

@router.message(
    ReceiptState.waiting_receipt,
    F.photo,
)
async def receipt_handler(
    message: Message,
    state: FSMContext,
):
    try:

        # --------------------------------
        # ПОЛУЧАЕМ ДАННЫЕ FSM
        # --------------------------------

        data = await state.get_data()

        room_id = data.get("room_id")

        if room_id is None:
            await message.answer(
                "❌ Комната не найдена."
            )
            return

        async with AsyncSessionLocal() as session:

            user = await UserRepository.get_by_telegram_id(
                session=session,
                telegram_id=message.from_user.id,
            )

            if user is None:
                await message.answer(
                    "❌ Пользователь не найден."
                )
                return

            permission = (
                await ReceiptPermissionService.can_manage(
                    session=session,
                    room_id=room_id,
                    user_id=user.id,
                )
            )

            if permission == ReceiptPermission.NOT_MEMBER:
                await message.answer(
                    "❌ Вы больше не участник этой комнаты."
                )
                await state.clear()
                return

        # --------------------------------
        # ПОЛУЧАЕМ ФОТО
        # --------------------------------

        photo = message.photo[-1]

        file = await message.bot.get_file(
            photo.file_id
        )

        file_name = (
            f"{photo.file_unique_id}.jpg"
        )

        destination = (
            RECEIPTS_DIR / file_name
        )

        await message.bot.download_file(
            file.file_path,
            destination=destination,
        )

        # --------------------------------
        # OCR
        # --------------------------------

        ocr = OCRService()

        result = ocr.process(
            str(destination)
        )

        # --------------------------------
        # СОХРАНЯЕМ ЧЕК
        # --------------------------------

        async with AsyncSessionLocal() as session:

            receipt = await ReceiptService.save_receipt(
                session=session,
                room_id=room_id,
                photo_path=str(destination),
                total=result.receipt.total,
            )

            # --------------------------------
            # ЕСЛИ СУММУ ОПРЕДЕЛИТЬ НЕ УДАЛОСЬ
            # --------------------------------

            if result.receipt.total is None:

                await session.commit()

                await state.update_data(
                    receipt_id=receipt.id,
                    room_id=room_id,
                )

                await state.set_state(
                    ReceiptState.waiting_total
                )

                await AnchorService.render(
                    bot=message.bot,
                    session=session,
                    room_id=room_id,
                    user_id=user.id,
                    text=(
                        "❌ Не удалось определить сумму чека.\n\n"
                        "Введите общую сумму вручную.\n\n"
                        "Например:\n"
                        "<code>123.45</code>"
                    ),
                )

                await session.commit()

            try:
                await message.delete()
            except Exception:
                logger.warning(
                    "Не удалось удалить сообщение с чеком",
                    exc_info=True,
                )

            if result.receipt.total is None:
                return

            # --------------------------------
            # ОБНОВЛЯЕМ ЭКРАНЫ ВСЕХ УЧАСТНИКОВ
            # --------------------------------

            room = await RoomService.get_by_id(
                session=session,
                room_id=room_id,
            )

            if room is None:
                await message.answer(
                    "❌ Комната не найдена."
                )
                await state.clear()
                return

            room_total = await ReceiptService.get_room_total(
                session=session,
                room_id=room_id,
            )

            members = await RoomMemberService.get_members(
                session=session,
                room_id=room_id,
            )

            banner = (
                "✅ Чек добавлен: "
                f"{result.receipt.total:.2f} zł"
            )

            async def render_menu_for(member_user_id):
                return build_menu_screen(
                    room=room,
                    total=room_total,
                    members=members,
                    is_owner=(member_user_id == room.owner_id),
                    banner=banner if member_user_id == user.id else None,
                )

            await AnchorService.broadcast(
                bot=message.bot,
                session=session,
                room_id=room_id,
                render_fn=render_menu_for,
            )

            await session.commit()

        try:
            await message.delete()
        except Exception:
            logger.warning(
                "Не удалось удалить сообщение с чеком",
                exc_info=True,
            )

        # --------------------------------
        # СЛЕДУЮЩИЙ ЧЕК
        # --------------------------------

        await state.set_state(
            ReceiptState.waiting_receipt
        )

    except Exception as e:

        logger.exception("Ошибка при обработке чека")

        # Ошибка также относится к текущему процессу комнаты,
        # но room_id может быть недоступен, поэтому просто
        # отправляем сообщение без сохранения.

        await message.answer(
            f"❌ Ошибка: {e}"
        )


# ============================================================
# РУЧНОЙ ВВОД СУММЫ ЧЕКА
# ============================================================

@router.message(
    ReceiptState.waiting_total,
    F.text,
)
async def manual_total(
    message: Message,
    state: FSMContext,
):
    try:

        # --------------------------------
        # ПОЛУЧАЕМ СУММУ
        # --------------------------------

        total = float(
            message.text.replace(",", ".")
        )

    except ValueError:

        await message.answer(
            "❌ Неверный формат.\n\n"
            "Введите сумму, например:\n"
            "<code>123.45</code>",
            parse_mode="HTML",
        )

        return

    data = await state.get_data()

    receipt_id = data.get(
        "receipt_id"
    )

    room_id = data.get(
        "room_id"
    )

    if receipt_id is None or room_id is None:

        await message.answer(
            "❌ Чек не найден."
        )

        await state.clear()

        return

    async with AsyncSessionLocal() as session:

        user = await UserRepository.get_by_telegram_id(
            session=session,
            telegram_id=message.from_user.id,
        )

        if user is None:
            await message.answer(
                "❌ Пользователь не найден."
            )
            await state.clear()
            return

        await ReceiptService.update_total(
            session=session,
            receipt_id=receipt_id,
            total=total,
        )

        room = await RoomService.get_by_id(
            session=session,
            room_id=room_id,
        )

        if room is None:
            await message.answer(
                "❌ Комната не найдена."
            )
            await state.clear()
            return

        room_total = await ReceiptService.get_room_total(
            session=session,
            room_id=room_id,
        )

        members = await RoomMemberService.get_members(
            session=session,
            room_id=room_id,
        )

        banner = f"✅ Чек добавлен: {total:.2f} zł"

        async def render_menu_for(member_user_id):
            return build_menu_screen(
                room=room,
                total=room_total,
                members=members,
                is_owner=(member_user_id == room.owner_id),
                banner=banner if member_user_id == user.id else None,
            )

        await AnchorService.broadcast(
            bot=message.bot,
            session=session,
            room_id=room_id,
            render_fn=render_menu_for,
        )

        await session.commit()

    try:
        await message.delete()
    except Exception:
        logger.warning(
            "Не удалось удалить сообщение с суммой",
            exc_info=True,
        )

    await state.set_state(
        ReceiptState.waiting_receipt
    )
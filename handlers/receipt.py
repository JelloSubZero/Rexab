import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from services.receipt_permission_service import (
    ReceiptPermission,
    ReceiptPermissionService,
)

from repositories.user_repository import UserRepository

from services.room_view_service import RoomViewService
from services.room_message_service import RoomMessageService

from keyboards.receipt_menu import receipt_menu

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

                # Фиксируем Receipt,
                # потому что его ID нужен
                # следующему FSM-состоянию.
                await session.commit()

                await state.update_data(
                    receipt_id=receipt.id,
                    room_id=room_id,
                )

                await state.set_state(
                    ReceiptState.waiting_total
                )

                sent_message = await message.answer(
                    "❌ Не удалось определить сумму чека.\n\n"
                    "Введите общую сумму вручную.\n\n"
                    "Например:\n"
                    "<code>123.45</code>",
                    parse_mode="HTML",
                )

                # Сохраняем сообщение в room_messages
                async with AsyncSessionLocal() as message_session:

                    await RoomMessageService.save(
                        session=message_session,
                        room_id=room_id,
                        chat_id=sent_message.chat.id,
                        message_id=sent_message.message_id,
                    )

                    await message_session.commit()

                return

            # --------------------------------
            # ПОЛУЧАЕМ ОБЩУЮ СУММУ КОМНАТЫ
            # --------------------------------

            room_total = await ReceiptService.get_room_total(
                session=session,
                room_id=room_id,
            )

            # --------------------------------
            # ОБНОВЛЯЕМ ОСНОВНОЙ ЭКРАН КОМНАТЫ
            # --------------------------------

            await RoomViewService.refresh_room(
                bot=message.bot,
                session=session,
                room_id=room_id,
            )

            # --------------------------------
            # СООБЩЕНИЕ О ДОБАВЛЕНИИ ЧЕКА
            # --------------------------------

            sent_message = await message.answer(
                "✅ <b>Чек добавлен.</b>\n\n"
                f"🧾 Сумма этого чека: "
                f"<b>{result.receipt.total:.2f} zł</b>\n"
                f"💰 Общая сумма комнаты: "
                f"<b>{room_total:.2f} zł</b>",
                parse_mode="HTML",
                reply_markup=receipt_menu(room_id),
            )

            # --------------------------------
            # СОХРАНЯЕМ MESSAGE_ID
            # --------------------------------

            await RoomMessageService.save(
                session=session,
                room_id=room_id,
                chat_id=sent_message.chat.id,
                message_id=sent_message.message_id,
            )

            # --------------------------------
            # ФИКСИРУЕМ ТРАНЗАКЦИЮ
            # --------------------------------

            await session.commit()

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

    # --------------------------------
    # ПОЛУЧАЕМ ДАННЫЕ FSM
    # --------------------------------

    data = await state.get_data()

    receipt_id = data.get(
        "receipt_id"
    )

    if receipt_id is None:

        await message.answer(
            "❌ Чек не найден."
        )

        await state.clear()

        return

    # --------------------------------
    # ОБНОВЛЯЕМ ЧЕК
    # --------------------------------

    async with AsyncSessionLocal() as session:

        receipt = await ReceiptService.update_total(
            session=session,
            receipt_id=receipt_id,
            total=total,
        )

        if receipt is None:
            await message.answer(
                "❌ Чек не найден."
            )
            await state.clear()
            return

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

        permission = await ReceiptPermissionService.can_manage(
            session=session,
            room_id=receipt.room_id,
            user_id=user.id,
        )

        if permission == ReceiptPermission.NOT_MEMBER:
            await message.answer(
                "❌ Вы больше не участник этой комнаты."
            )
            await state.clear()
            return

            await message.answer(
                "❌ Чек не найден."
            )

            await state.clear()

            return

        room_total = (
            await ReceiptService.get_room_total(
                session=session,
                room_id=receipt.room_id,
            )
        )

        # --------------------------------
        # ОБНОВЛЯЕМ ОСНОВНОЙ ЭКРАН КОМНАТЫ
        # --------------------------------

        await RoomViewService.refresh_room(
            bot=message.bot,
            session=session,
            room_id=receipt.room_id,
        )

        # --------------------------------
        # СООБЩЕНИЕ "СУММА СОХРАНЕНА"
        # --------------------------------

        sent_message = await message.answer(
            "✅ <b>Сумма сохранена.</b>\n\n"
            f"🧾 Сумма этого чека: "
            f"<b>{total:.2f} zł</b>\n"
            f"💰 Общая сумма комнаты: "
            f"<b>{room_total:.2f} zł</b>",
            parse_mode="HTML",
            reply_markup=receipt_menu(
                receipt.room_id
            ),
        )

        # --------------------------------
        # СОХРАНЯЕМ MESSAGE_ID
        # --------------------------------

        await RoomMessageService.save(
            session=session,
            room_id=receipt.room_id,
            chat_id=sent_message.chat.id,
            message_id=sent_message.message_id,
        )

        # --------------------------------
        # ФИКСИРУЕМ ТРАНЗАКЦИЮ
        # --------------------------------

        await session.commit()

    # --------------------------------
    # СОХРАНЯЕМ ROOM_ID В FSM
    # --------------------------------

    await state.update_data(
        room_id=receipt.room_id,
    )

    # --------------------------------
    # СНОВА ЖДЁМ ФОТО ЧЕКА
    # --------------------------------

    await state.set_state(
        ReceiptState.waiting_receipt
    )
from aiogram import Bot


class NotificationService:

    @staticmethod
    async def notify_payment_added(
        bot: Bot,
        telegram_ids: list[int],
        payer_name: str,
        description: str,
        amount: float,
    ):
        """
        Уведомляет участников комнаты
        о добавлении нового платежа.
        """

        text = (
            "💳 <b>Новый расход</b>\n\n"
            f"👤 {payer_name} добавил расход:\n"
            f"📝 {description}\n"
            f"💰 <b>{amount:.2f} zł</b>"
        )

        for telegram_id in telegram_ids:

            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    parse_mode="HTML",
                )

            except Exception as e:
                print(
                    f"❌ Не удалось отправить "
                    f"уведомление пользователю "
                    f"{telegram_id}: {e}"
                )


    @staticmethod
    async def notify_payment_deleted(
        bot: Bot,
        telegram_ids: list[int],
        user_name: str,
        description: str,
        amount: float,
    ):
        text = (
            "🗑 <b>Расход удалён</b>\n\n"
            f"👤 {user_name} удалил расход:\n"
            f"📝 {description}\n"
            f"💰 <b>{amount:.2f} zł</b>"
        )

        for telegram_id in telegram_ids:

            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    parse_mode="HTML",
                )

            except Exception as e:
                print(
                    f"❌ Не удалось отправить "
                    f"уведомление пользователю "
                    f"{telegram_id}: {e}"
                )


    @staticmethod
    async def notify_member_joined(
        bot: Bot,
        telegram_ids: list[int],
        member_name: str,
    ):
        """
        Уведомляет участников комнаты
        о присоединении нового пользователя.
        """

        text = (
            "👋 <b>Новый участник</b>\n\n"
            f"👤 <b>{member_name}</b> "
            "присоединился к комнате."
        )

        for telegram_id in telegram_ids:

            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    parse_mode="HTML",
                )

            except Exception as e:
                print(
                    f"❌ Не удалось отправить "
                    f"уведомление пользователю "
                    f"{telegram_id}: {e}"
                )


    @staticmethod
    async def notify_member_removed(
        bot: Bot,
        telegram_ids: list[int],
        member_name: str,
    ):
        """
        Уведомляет участников комнаты
        о выходе пользователя.
        """

        text = (
            "👋 <b>Участник вышел</b>\n\n"
            f"👤 <b>{member_name}</b> "
            "покинул комнату."
        )

        for telegram_id in telegram_ids:

            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    parse_mode="HTML",
                )

            except Exception as e:
                print(
                    f"❌ Не удалось отправить "
                    f"уведомление пользователю "
                    f"{telegram_id}: {e}"
                )

    @staticmethod
    async def notify_debt_changed(
        bot: Bot,
        telegram_id: int,
        payer_name: str,
        description: str,
        amount: float,
        share: float,
        balance: float,
    ):
        """
        Персонально уведомляет пользователя
        об изменении его баланса после расхода.
        """

        if balance > 0:
            balance_text = (
                f"🟢 Тебе должны: "
                f"<b>{balance:.2f} zł</b>"
            )

        elif balance < 0:
            balance_text = (
                f"🔴 Ты должен: "
                f"<b>{abs(balance):.2f} zł</b>"
            )

        else:
            balance_text = (
                "⚪ Баланс: <b>0.00 zł</b>"
            )

        # Если пользователь сам добавил расход
        if payer_name:
            text = (
                "💳 <b>Новый расход</b>\n\n"
                f"👤 <b>{payer_name}</b> добавил:\n"
                f"📝 {description}\n"
                f"💰 <b>{amount:.2f} zł</b>\n\n"
                f"💵 Твоя доля: "
                f"<b>{share:.2f} zł</b>\n"
                f"{balance_text}"
            )

        else:
            text = (
                "💸 <b>Баланс изменён</b>\n\n"
                f"📝 {description}\n"
                f"💰 <b>{amount:.2f} zł</b>\n\n"
                f"💵 Твоя доля: "
                f"<b>{share:.2f} zł</b>\n"
                f"{balance_text}"
            )

        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=text,
                parse_mode="HTML",
            )

        except Exception as e:
            print(
                f"❌ Не удалось отправить "
                f"уведомление пользователю "
                f"{telegram_id}: {e}"
            )

    @staticmethod
    async def notify_debt_changed_after_delete(
        bot: Bot,
        telegram_id: int,
        user_name: str,
        description: str,
        amount: float,
        share: float,
        balance: float,
    ):
        """
        Уведомляет пользователя об удалении расхода
        и показывает его новый баланс.
        """

        if balance > 0:
            balance_text = (
                f"🟢 Тебе должны: "
                f"<b>{balance:.2f} zł</b>"
            )

        elif balance < 0:
            balance_text = (
                f"🔴 Ты должен: "
                f"<b>{abs(balance):.2f} zł</b>"
            )

        else:
            balance_text = (
                "⚪ Баланс: <b>0.00 zł</b>"
            )

        text = (
            "🗑 <b>Расход удалён</b>\n\n"
            f"👤 <b>{user_name}</b> удалил:\n"
            f"📝 {description}\n"
            f"💰 <b>{amount:.2f} zł</b>\n\n"
            f"💵 Твоя доля: "
            f"<b>{share:.2f} zł</b>\n"
            f"{balance_text}"
        )

        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=text,
                parse_mode="HTML",
            )

        except Exception as e:
            print(
                f"❌ Не удалось отправить "
                f"уведомление пользователю "
                f"{telegram_id}: {e}"
            )
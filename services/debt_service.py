from decimal import Decimal, ROUND_HALF_UP


class DebtService:

    @staticmethod
    def calculate(
        members,
        payments,
    ):
        """
        Рассчитывает минимальное количество переводов.

        Все расходы делятся поровну между всеми
        участниками комнаты.
        """

        if not members:
            return []

        member_ids = [
            member.user_id
            for member in members
        ]

        # Переводим всё в копейки,
        # чтобы избежать ошибок float.
        total_cents = sum(
            int(
                (
                    Decimal(str(payment.amount))
                    * 100
                ).quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP,
                )
            )
            for payment in payments
        )

        if total_cents <= 0:
            return []

        member_count = len(member_ids)

        # Базовая доля в копейках
        base_share = total_cents // member_count

        # Остаток копеек
        remainder = total_cents % member_count

        # Балансы в копейках
        balances = {}

        for index, user_id in enumerate(member_ids):
            share = base_share

            # Распределяем остаток по 1 копейке
            if index < remainder:
                share += 1

            balances[user_id] = -share

        # Добавляем фактически оплаченные суммы
        for payment in payments:

            if payment.user_id not in balances:
                continue

            amount_cents = int(
                (
                    Decimal(str(payment.amount))
                    * 100
                ).quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP,
                )
            )

            balances[payment.user_id] += amount_cents

        creditors = []
        debtors = []

        for user_id, balance in balances.items():

            if balance > 0:
                creditors.append(
                    {
                        "user_id": user_id,
                        "amount": balance,
                    }
                )

            elif balance < 0:
                debtors.append(
                    {
                        "user_id": user_id,
                        "amount": -balance,
                    }
                )

        transfers = []

        creditor_index = 0
        debtor_index = 0

        while (
            creditor_index < len(creditors)
            and debtor_index < len(debtors)
        ):
            creditor = creditors[creditor_index]
            debtor = debtors[debtor_index]

            amount = min(
                creditor["amount"],
                debtor["amount"],
            )

            if amount > 0:
                transfers.append(
                    {
                        "from_user_id": debtor["user_id"],
                        "to_user_id": creditor["user_id"],
                        "amount": Decimal(amount) / 100,
                    }
                )

            creditor["amount"] -= amount
            debtor["amount"] -= amount

            if creditor["amount"] == 0:
                creditor_index += 1

            if debtor["amount"] == 0:
                debtor_index += 1

        return transfers
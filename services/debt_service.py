from decimal import Decimal, ROUND_HALF_UP


class DebtService:

    @staticmethod
    def _to_cents(amount):
        return int(
            (
                Decimal(str(amount)) * 100
            ).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )
        )

    @staticmethod
    def _build_balances(
        members,
        payments,
        settlements=None,
    ):
        """
        Строит актуальные балансы участников.

        payments:
            расходы комнаты.

        settlements:
            подтверждённые погашения.

        pending settlement НЕ учитывается.
        """

        if not members:
            return {}, 0, 0

        member_ids = [
            member.user_id
            for member in members
        ]

        # --------------------------------
        # ОБЩАЯ СУММА РАСХОДОВ
        # --------------------------------

        total_cents = sum(
            DebtService._to_cents(
                payment.amount
            )
            for payment in payments
        )

        if total_cents <= 0:
            return (
                {
                    user_id: 0
                    for user_id in member_ids
                },
                0,
                0,
            )

        member_count = len(member_ids)

        # --------------------------------
        # ДОЛЯ КАЖДОГО
        # --------------------------------

        base_share = (
            total_cents // member_count
        )

        remainder = (
            total_cents % member_count
        )

        # --------------------------------
        # НАЧАЛЬНЫЕ БАЛАНСЫ
        # --------------------------------

        balances = {}

        for index, user_id in enumerate(
            member_ids
        ):

            share = base_share

            if index < remainder:
                share += 1

            balances[user_id] = -share

        # --------------------------------
        # ДОБАВЛЯЕМ ФАКТИЧЕСКИЕ ПЛАТЕЖИ
        # --------------------------------

        for payment in payments:

            if payment.user_id not in balances:
                continue

            amount_cents = (
                DebtService._to_cents(
                    payment.amount
                )
            )

            balances[payment.user_id] += (
                amount_cents
            )

        # --------------------------------
        # УЧИТЫВАЕМ ПОДТВЕРЖДЁННЫЕ
        # ПОГАШЕНИЯ
        # --------------------------------

        if settlements:

            for settlement in settlements:

                if settlement.status != "confirmed":
                    continue

                from_user_id = (
                    settlement.from_user_id
                )

                to_user_id = (
                    settlement.to_user_id
                )

                amount_cents = (
                    DebtService._to_cents(
                        settlement.amount
                    )
                )

                # Должник передал деньги.
                #
                # Его долг уменьшается:
                # -100 -> 0
                #
                # Поэтому добавляем сумму.
                if from_user_id in balances:
                    balances[from_user_id] += (
                        amount_cents
                    )

                # Получатель получил деньги.
                #
                # Его кредит уменьшается:
                # +100 -> 0
                #
                # Поэтому вычитаем сумму.
                if to_user_id in balances:
                    balances[to_user_id] -= (
                        amount_cents
                    )

        return (
            balances,
            total_cents,
            base_share,
        )

    @staticmethod
    def _build_transfers(
        balances,
    ):
        """
        Превращает балансы в минимальное
        количество переводов.
        """

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

            creditor = creditors[
                creditor_index
            ]

            debtor = debtors[
                debtor_index
            ]

            amount = min(
                creditor["amount"],
                debtor["amount"],
            )

            if amount > 0:

                transfers.append(
                    {
                        "from_user_id": (
                            debtor["user_id"]
                        ),
                        "to_user_id": (
                            creditor["user_id"]
                        ),
                        "amount": (
                            Decimal(amount) / 100
                        ),
                    }
                )

            creditor["amount"] -= amount
            debtor["amount"] -= amount

            if creditor["amount"] == 0:
                creditor_index += 1

            if debtor["amount"] == 0:
                debtor_index += 1

        return transfers

    @staticmethod
    def calculate(
        members,
        payments,
        settlements=None,
    ):
        """
        Рассчитывает минимальное количество переводов.

        settlements должен содержать подтверждённые
        погашения.

        Pending погашения игнорируются.
        """

        if not members:
            return []

        (
            balances,
            total_cents,
            _,
        ) = DebtService._build_balances(
            members=members,
            payments=payments,
            settlements=settlements,
        )

        if total_cents <= 0:
            return []

        return DebtService._build_transfers(
            balances=balances,
        )

    @staticmethod
    def calculate_details(
        members,
        payments,
        settlements=None,
    ):
        """
        Полный расчёт долгов.

        Возвращает:

        total
        share
        balances
        transfers
        """

        if not members:

            return {
                "total": Decimal("0.00"),
                "share": Decimal("0.00"),
                "balances": {},
                "transfers": [],
            }

        (
            balances_cents,
            total_cents,
            _,
        ) = DebtService._build_balances(
            members=members,
            payments=payments,
            settlements=settlements,
        )

        if total_cents <= 0:

            return {
                "total": Decimal("0.00"),
                "share": Decimal("0.00"),
                "balances": {
                    member.user_id: Decimal("0.00")
                    for member in members
                },
                "transfers": [],
            }

        member_count = len(members)

        # --------------------------------
        # ОБЩАЯ СУММА
        # --------------------------------

        total = (
            Decimal(total_cents) / 100
        )

        # --------------------------------
        # ДОЛЯ
        # --------------------------------

        share = (
            Decimal(total_cents)
            / Decimal(member_count)
            / Decimal("100")
        )

        share = share.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        # --------------------------------
        # БАЛАНСЫ В ZŁ
        # --------------------------------

        balances = {
            user_id: (
                Decimal(balance) / 100
            )
            for user_id, balance
            in balances_cents.items()
        }

        # --------------------------------
        # ПЕРЕВОДЫ
        # --------------------------------

        transfers = (
            DebtService._build_transfers(
                balances=balances_cents,
            )
        )

        return {
            "total": total,
            "share": share,
            "balances": balances,
            "transfers": transfers,
        }
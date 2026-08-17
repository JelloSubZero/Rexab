from types import SimpleNamespace
from decimal import Decimal

from services.debt_service import DebtService


def make_members(*user_ids):
    return [
        SimpleNamespace(user_id=user_id)
        for user_id in user_ids
    ]


def make_payment(user_id, amount):
    return SimpleNamespace(
        user_id=user_id,
        amount=amount,
    )


def make_settlement(
    from_user_id,
    to_user_id,
    amount,
    status="confirmed",
):
    return SimpleNamespace(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        amount=amount,
        status=status,
    )


def test_two_members_one_payer():
    members = make_members(1, 2)
    payments = [
        make_payment(1, 100),
    ]

    result = DebtService.calculate_details(
        members=members,
        payments=payments,
    )

    assert result["total"] == Decimal("100.00")
    assert result["share"] == Decimal("50.00")

    assert result["balances"][1] == Decimal("50.00")
    assert result["balances"][2] == Decimal("-50.00")

    assert result["transfers"] == [
        {
            "from_user_id": 2,
            "to_user_id": 1,
            "amount": Decimal("50"),
        }
    ]


def test_pending_settlement_does_not_change_debt():
    members = make_members(1, 2)

    payments = [
        make_payment(1, 100),
    ]

    settlements = [
        make_settlement(
            2,
            1,
            50,
            status="pending",
        )
    ]

    result = DebtService.calculate_details(
        members=members,
        payments=payments,
        settlements=settlements,
    )

    assert result["balances"][1] == Decimal("50.00")
    assert result["balances"][2] == Decimal("-50.00")


def test_confirmed_settlement_clears_debt():
    members = make_members(1, 2)

    payments = [
        make_payment(1, 100),
    ]

    settlements = [
        make_settlement(
            2,
            1,
            50,
            status="confirmed",
        )
    ]

    result = DebtService.calculate_details(
        members=members,
        payments=payments,
        settlements=settlements,
    )

    assert result["balances"][1] == Decimal("0.00")
    assert result["balances"][2] == Decimal("0.00")
    assert result["transfers"] == []


def test_uneven_split_is_distributed_in_cents():
    members = make_members(1, 2, 3)

    payments = [
        make_payment(1, 100),
    ]

    result = DebtService.calculate_details(
        members=members,
        payments=payments,
    )

    assert result["balances"] == {
        1: Decimal("66.66"),
        2: Decimal("-33.33"),
        3: Decimal("-33.33"),
    }

    assert result["transfers"] == [
        {
            "from_user_id": 2,
            "to_user_id": 1,
            "amount": Decimal("33.33"),
        },
        {
            "from_user_id": 3,
            "to_user_id": 1,
            "amount": Decimal("33.33"),
        },
    ]
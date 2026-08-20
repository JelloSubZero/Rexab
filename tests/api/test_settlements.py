def _register_and_token(client, email, first_name="User"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "first_name": first_name,
        },
    )

    body = response.json()

    return body["access_token"], body["user"]["id"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _room_with_debt(client):
    """
    Owner pays 100 in a 2-person room -> member owes owner 50.
    """
    owner_token, owner_id = _register_and_token(
        client, "owner@example.com", "Owner"
    )
    member_token, member_id = _register_and_token(
        client, "member@example.com", "Member"
    )

    room = client.post(
        "/api/rooms",
        json={"name": "Apartment"},
        headers=_auth_headers(owner_token),
    ).json()

    client.post(
        "/api/rooms/join",
        json={"code": room["code"]},
        headers=_auth_headers(member_token),
    )

    client.post(
        f"/api/rooms/{room['id']}/payments",
        json={"user_id": owner_id, "amount": 100},
        headers=_auth_headers(owner_token),
    )

    return room, owner_token, owner_id, member_token, member_id


def test_create_settlement_with_correct_amount(client):
    room, owner_token, owner_id, member_token, member_id = (
        _room_with_debt(client)
    )

    response = client.post(
        f"/api/rooms/{room['id']}/settlements",
        json={
            "from_user_id": member_id,
            "to_user_id": owner_id,
            "amount": 50,
        },
        headers=_auth_headers(member_token),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["status"] == "pending"
    assert body["amount"] == 50


def test_create_settlement_rejects_stale_amount(client):
    room, owner_token, owner_id, member_token, member_id = (
        _room_with_debt(client)
    )

    response = client.post(
        f"/api/rooms/{room['id']}/settlements",
        json={
            "from_user_id": member_id,
            "to_user_id": owner_id,
            "amount": 999,
        },
        headers=_auth_headers(member_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "AMOUNT_OUT_OF_DATE"


def test_create_settlement_same_user_rejected(client):
    room, owner_token, owner_id, _, _ = _room_with_debt(client)

    response = client.post(
        f"/api/rooms/{room['id']}/settlements",
        json={
            "from_user_id": owner_id,
            "to_user_id": owner_id,
            "amount": 50,
        },
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SAME_USER"


def test_duplicate_pending_settlement_rejected(client):
    room, owner_token, owner_id, member_token, member_id = (
        _room_with_debt(client)
    )

    body = {
        "from_user_id": member_id,
        "to_user_id": owner_id,
        "amount": 50,
    }

    client.post(
        f"/api/rooms/{room['id']}/settlements",
        json=body,
        headers=_auth_headers(member_token),
    )

    response = client.post(
        f"/api/rooms/{room['id']}/settlements",
        json=body,
        headers=_auth_headers(member_token),
    )

    assert response.status_code == 409
    assert (
        response.json()["error"]["code"]
        == "SETTLEMENT_ALREADY_PENDING"
    )


def test_only_receiver_can_confirm(client):
    room, owner_token, owner_id, member_token, member_id = (
        _room_with_debt(client)
    )

    settlement = client.post(
        f"/api/rooms/{room['id']}/settlements",
        json={
            "from_user_id": member_id,
            "to_user_id": owner_id,
            "amount": 50,
        },
        headers=_auth_headers(member_token),
    ).json()

    forbidden = client.post(
        f"/api/settlements/{settlement['id']}/confirm",
        headers=_auth_headers(member_token),
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "NOT_RECEIVER"

    allowed = client.post(
        f"/api/settlements/{settlement['id']}/confirm",
        headers=_auth_headers(owner_token),
    )

    assert allowed.status_code == 200
    assert allowed.json()["status"] == "confirmed"


def test_cannot_confirm_twice(client):
    room, owner_token, owner_id, member_token, member_id = (
        _room_with_debt(client)
    )

    settlement = client.post(
        f"/api/rooms/{room['id']}/settlements",
        json={
            "from_user_id": member_id,
            "to_user_id": owner_id,
            "amount": 50,
        },
        headers=_auth_headers(member_token),
    ).json()

    client.post(
        f"/api/settlements/{settlement['id']}/confirm",
        headers=_auth_headers(owner_token),
    )

    response = client.post(
        f"/api/settlements/{settlement['id']}/confirm",
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ALREADY_CONFIRMED"


def test_list_settlements_requires_membership(client):
    room, owner_token, owner_id, member_token, member_id = (
        _room_with_debt(client)
    )

    client.post(
        f"/api/rooms/{room['id']}/settlements",
        json={
            "from_user_id": member_id,
            "to_user_id": owner_id,
            "amount": 50,
        },
        headers=_auth_headers(member_token),
    )

    outsider_token, _ = _register_and_token(
        client, "outsider@example.com"
    )

    forbidden = client.get(
        f"/api/rooms/{room['id']}/settlements",
        headers=_auth_headers(outsider_token),
    )

    assert forbidden.status_code == 403

    allowed = client.get(
        f"/api/rooms/{room['id']}/settlements",
        headers=_auth_headers(owner_token),
    )

    assert allowed.status_code == 200
    assert len(allowed.json()) == 1


def test_get_settlement_missing_is_404(client):
    _, owner_token, _, _, _ = _room_with_debt(client)

    response = client.get(
        "/api/settlements/999999",
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 404

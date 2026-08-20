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


def _create_room_with_member(client):
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

    return room, owner_token, owner_id, member_token, member_id


def test_create_payment(client):
    room, owner_token, owner_id, _, _ = _create_room_with_member(
        client
    )

    response = client.post(
        f"/api/rooms/{room['id']}/payments",
        json={
            "user_id": owner_id,
            "amount": 80,
            "description": "Dinner",
        },
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["amount"] == 80
    assert body["description"] == "Dinner"
    assert body["payer_name"] == "Owner"


def test_create_payment_requires_membership(client):
    room, _, owner_id, _, _ = _create_room_with_member(client)

    outsider_token, _ = _register_and_token(
        client, "outsider@example.com"
    )

    response = client.post(
        f"/api/rooms/{room['id']}/payments",
        json={"user_id": owner_id, "amount": 50},
        headers=_auth_headers(outsider_token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "NOT_ROOM_MEMBER"


def test_create_payment_payer_must_be_member(client):
    room, owner_token, _, _, _ = _create_room_with_member(client)

    outsider_token, outsider_id = _register_and_token(
        client, "outsider2@example.com"
    )

    response = client.post(
        f"/api/rooms/{room['id']}/payments",
        json={"user_id": outsider_id, "amount": 50},
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PAYER_NOT_MEMBER"


def test_create_payment_rejects_non_positive_amount(client):
    room, owner_token, owner_id, _, _ = _create_room_with_member(
        client
    )

    response = client.post(
        f"/api/rooms/{room['id']}/payments",
        json={"user_id": owner_id, "amount": 0},
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 422


def test_list_payments(client):
    room, owner_token, owner_id, _, _ = _create_room_with_member(
        client
    )

    client.post(
        f"/api/rooms/{room['id']}/payments",
        json={"user_id": owner_id, "amount": 30},
        headers=_auth_headers(owner_token),
    )
    client.post(
        f"/api/rooms/{room['id']}/payments",
        json={"user_id": owner_id, "amount": 20},
        headers=_auth_headers(owner_token),
    )

    response = client.get(
        f"/api/rooms/{room['id']}/payments",
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_single_payment_requires_membership(client):
    room, owner_token, owner_id, _, _ = _create_room_with_member(
        client
    )

    payment = client.post(
        f"/api/rooms/{room['id']}/payments",
        json={"user_id": owner_id, "amount": 30},
        headers=_auth_headers(owner_token),
    ).json()

    outsider_token, _ = _register_and_token(
        client, "outsider3@example.com"
    )

    forbidden = client.get(
        f"/api/payments/{payment['id']}",
        headers=_auth_headers(outsider_token),
    )

    assert forbidden.status_code == 403

    allowed = client.get(
        f"/api/payments/{payment['id']}",
        headers=_auth_headers(owner_token),
    )

    assert allowed.status_code == 200


def test_get_missing_payment_is_404(client):
    _, owner_token, _, _, _ = _create_room_with_member(client)

    response = client.get(
        "/api/payments/999999",
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PAYMENT_NOT_FOUND"

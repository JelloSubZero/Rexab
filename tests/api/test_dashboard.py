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


def test_dashboard_requires_membership(client):
    owner_token, owner_id = _register_and_token(
        client, "owner@example.com", "Owner"
    )

    room = client.post(
        "/api/rooms",
        json={"name": "Apartment"},
        headers=_auth_headers(owner_token),
    ).json()

    outsider_token, _ = _register_and_token(
        client, "outsider@example.com"
    )

    response = client.get(
        f"/api/rooms/{room['id']}/dashboard",
        headers=_auth_headers(outsider_token),
    )

    assert response.status_code == 403


def test_dashboard_reflects_real_balances(client):
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
        json={
            "user_id": owner_id,
            "amount": 100,
            "description": "Dinner",
        },
        headers=_auth_headers(owner_token),
    )

    owner_dashboard = client.get(
        f"/api/rooms/{room['id']}/dashboard",
        headers=_auth_headers(owner_token),
    ).json()

    member_dashboard = client.get(
        f"/api/rooms/{room['id']}/dashboard",
        headers=_auth_headers(member_token),
    ).json()

    assert owner_dashboard["balance"] == 50
    assert owner_dashboard["you_are_owed"] == 50
    assert owner_dashboard["transfers"] == [
        {
            "from_user_id": member_id,
            "to_user_id": owner_id,
            "amount": 50,
        }
    ]
    assert owner_dashboard["you_owe"] == 0
    assert owner_dashboard["members_count"] == 2

    assert member_dashboard["balance"] == -50
    assert member_dashboard["you_owe"] == 50
    assert member_dashboard["you_are_owed"] == 0

    assert len(owner_dashboard["recent_payments"]) == 1
    assert owner_dashboard["recent_payments"][0]["amount"] == 100


def test_dashboard_counts_pending_settlements(client):
    owner_token, owner_id = _register_and_token(
        client, "owner2@example.com", "Owner"
    )
    member_token, member_id = _register_and_token(
        client, "member2@example.com", "Member"
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

    client.post(
        f"/api/rooms/{room['id']}/settlements",
        json={
            "from_user_id": member_id,
            "to_user_id": owner_id,
            "amount": 50,
        },
        headers=_auth_headers(member_token),
    )

    dashboard = client.get(
        f"/api/rooms/{room['id']}/dashboard",
        headers=_auth_headers(owner_token),
    ).json()

    assert dashboard["pending_settlements"] == 1


def test_dashboard_zero_state_for_empty_room(client):
    owner_token, _ = _register_and_token(
        client, "owner3@example.com", "Owner"
    )

    room = client.post(
        "/api/rooms",
        json={"name": "Empty"},
        headers=_auth_headers(owner_token),
    ).json()

    dashboard = client.get(
        f"/api/rooms/{room['id']}/dashboard",
        headers=_auth_headers(owner_token),
    ).json()

    assert dashboard["balance"] == 0
    assert dashboard["you_owe"] == 0
    assert dashboard["you_are_owed"] == 0
    assert dashboard["recent_payments"] == []
    assert dashboard["pending_settlements"] == 0

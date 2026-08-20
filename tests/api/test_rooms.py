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


def test_create_room_returns_room_with_owner(client):
    token, _ = _register_and_token(client, "owner@example.com")

    response = client.post(
        "/api/rooms",
        json={"name": "Apartment"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Apartment"
    assert body["is_owner"] is True
    assert body["members_count"] == 1
    assert body["status"] == "active"


def test_list_rooms_only_returns_rooms_user_belongs_to(client):
    owner_token, _ = _register_and_token(client, "owner2@example.com")
    other_token, _ = _register_and_token(client, "other@example.com")

    client.post(
        "/api/rooms",
        json={"name": "Apartment"},
        headers=_auth_headers(owner_token),
    )

    owner_rooms = client.get(
        "/api/rooms", headers=_auth_headers(owner_token)
    ).json()
    other_rooms = client.get(
        "/api/rooms", headers=_auth_headers(other_token)
    ).json()

    assert len(owner_rooms) == 1
    assert len(other_rooms) == 0


def test_get_room_requires_membership(client):
    owner_token, _ = _register_and_token(client, "owner3@example.com")
    other_token, _ = _register_and_token(client, "other3@example.com")

    room = client.post(
        "/api/rooms",
        json={"name": "Apartment"},
        headers=_auth_headers(owner_token),
    ).json()

    forbidden = client.get(
        f"/api/rooms/{room['id']}",
        headers=_auth_headers(other_token),
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "NOT_ROOM_MEMBER"

    allowed = client.get(
        f"/api/rooms/{room['id']}",
        headers=_auth_headers(owner_token),
    )

    assert allowed.status_code == 200


def test_join_room_by_code(client):
    owner_token, _ = _register_and_token(client, "owner4@example.com")
    joiner_token, _ = _register_and_token(client, "joiner4@example.com")

    room = client.post(
        "/api/rooms",
        json={"name": "Trip"},
        headers=_auth_headers(owner_token),
    ).json()

    response = client.post(
        "/api/rooms/join",
        json={"code": room["code"]},
        headers=_auth_headers(joiner_token),
    )

    assert response.status_code == 200
    assert response.json()["members_count"] == 2


def test_join_room_with_unknown_code_is_404(client):
    token, _ = _register_and_token(client, "joiner5@example.com")

    response = client.post(
        "/api/rooms/join",
        json={"code": "NOPE0000"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ROOM_NOT_FOUND"


def test_leave_room_removes_member(client):
    owner_token, _ = _register_and_token(client, "owner6@example.com")
    joiner_token, _ = _register_and_token(client, "joiner6@example.com")

    room = client.post(
        "/api/rooms",
        json={"name": "Trip"},
        headers=_auth_headers(owner_token),
    ).json()

    client.post(
        "/api/rooms/join",
        json={"code": room["code"]},
        headers=_auth_headers(joiner_token),
    )

    response = client.post(
        f"/api/rooms/{room['id']}/leave",
        headers=_auth_headers(joiner_token),
    )

    assert response.status_code == 204

    remaining = client.get(
        f"/api/rooms/{room['id']}",
        headers=_auth_headers(owner_token),
    ).json()

    assert remaining["members_count"] == 1


def test_owner_cannot_leave_room(client):
    owner_token, _ = _register_and_token(client, "owner7@example.com")

    room = client.post(
        "/api/rooms",
        json={"name": "Trip"},
        headers=_auth_headers(owner_token),
    ).json()

    response = client.post(
        f"/api/rooms/{room['id']}/leave",
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "OWNER_CANNOT_LEAVE"


def test_delete_room_requires_ownership(client):
    owner_token, _ = _register_and_token(client, "owner8@example.com")
    other_token, _ = _register_and_token(client, "other8@example.com")

    room = client.post(
        "/api/rooms",
        json={"name": "Trip"},
        headers=_auth_headers(owner_token),
    ).json()

    forbidden = client.delete(
        f"/api/rooms/{room['id']}",
        headers=_auth_headers(other_token),
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "NOT_ROOM_OWNER"


def test_owner_can_delete_room(client):
    owner_token, _ = _register_and_token(client, "owner9@example.com")

    room = client.post(
        "/api/rooms",
        json={"name": "Trip"},
        headers=_auth_headers(owner_token),
    ).json()

    response = client.delete(
        f"/api/rooms/{room['id']}",
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 204

    after = client.get(
        f"/api/rooms/{room['id']}",
        headers=_auth_headers(owner_token),
    )

    assert after.status_code == 404

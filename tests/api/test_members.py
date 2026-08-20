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


def test_list_members_requires_membership(client):
    room, owner_token, _, _, _ = _create_room_with_member(client)

    outsider_token, _ = _register_and_token(
        client, "outsider@example.com"
    )

    forbidden = client.get(
        f"/api/rooms/{room['id']}/members",
        headers=_auth_headers(outsider_token),
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "NOT_ROOM_MEMBER"


def test_list_members_marks_owner(client):
    room, owner_token, owner_id, _, member_id = (
        _create_room_with_member(client)
    )

    response = client.get(
        f"/api/rooms/{room['id']}/members",
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 200

    members = {m["user_id"]: m for m in response.json()}

    assert members[owner_id]["is_owner"] is True
    assert members[member_id]["is_owner"] is False


def test_owner_can_remove_member(client):
    room, owner_token, _, _, member_id = _create_room_with_member(
        client
    )

    response = client.delete(
        f"/api/rooms/{room['id']}/members/{member_id}",
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 204

    remaining = client.get(
        f"/api/rooms/{room['id']}/members",
        headers=_auth_headers(owner_token),
    ).json()

    assert len(remaining) == 1


def test_non_owner_cannot_remove_member(client):
    room, _, _, member_token, member_id = _create_room_with_member(
        client
    )

    response = client.delete(
        f"/api/rooms/{room['id']}/members/{member_id}",
        headers=_auth_headers(member_token),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "NOT_ROOM_OWNER"


def test_owner_cannot_be_removed(client):
    room, owner_token, owner_id, _, _ = _create_room_with_member(
        client
    )

    response = client.delete(
        f"/api/rooms/{room['id']}/members/{owner_id}",
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 409
    assert (
        response.json()["error"]["code"] == "OWNER_CANNOT_BE_REMOVED"
    )

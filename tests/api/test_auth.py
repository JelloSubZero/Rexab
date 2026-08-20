import hashlib
import hmac
import time

import api.routers.auth as auth_router


def _register(client, email="alex@example.com", password="password123"):
    return client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Alex",
        },
    )


def test_register_returns_token_and_user(client):
    response = _register(client)

    assert response.status_code == 201

    body = response.json()

    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "alex@example.com"
    assert body["user"]["telegram_id"] is None


def test_register_duplicate_email_is_rejected(client):
    _register(client)

    response = _register(client)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_TAKEN"


def test_login_with_correct_password(client):
    _register(client)

    response = client.post(
        "/api/auth/login",
        json={
            "email": "alex@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_is_rejected(client):
    _register(client)

    response = client.post(
        "/api/auth/login",
        json={
            "email": "alex@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_me_returns_current_user(client):
    token = _register(client).json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "alex@example.com"


def test_logout_requires_authentication_and_returns_no_content(client):
    token = _register(client).json()["access_token"]

    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204


def _sign_telegram_payload(payload: dict, bot_token: str) -> dict:
    check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(payload.items())
    )

    secret_key = hashlib.sha256(bot_token.encode()).digest()

    signed_hash = hmac.new(
        secret_key,
        check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    return {**payload, "hash": signed_hash}


def test_telegram_login_with_valid_signature(client, monkeypatch):
    monkeypatch.setattr(auth_router, "BOT_TOKEN", "test-bot-token")

    payload = _sign_telegram_payload(
        {
            "id": 555,
            "first_name": "Daniel",
            "auth_date": int(time.time()),
        },
        "test-bot-token",
    )

    response = client.post("/api/auth/telegram", json=payload)

    assert response.status_code == 200

    body = response.json()

    assert body["user"]["telegram_id"] == 555
    assert body["user"]["first_name"] == "Daniel"


def test_telegram_login_rejects_bad_signature(client, monkeypatch):
    monkeypatch.setattr(auth_router, "BOT_TOKEN", "test-bot-token")

    payload = {
        "id": 555,
        "first_name": "Daniel",
        "auth_date": int(time.time()),
        "hash": "not-a-real-signature",
    }

    response = client.post("/api/auth/telegram", json=payload)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TELEGRAM_AUTH"


def test_telegram_login_not_configured_without_bot_token(
    client, monkeypatch
):
    monkeypatch.setattr(auth_router, "BOT_TOKEN", None)

    response = client.post(
        "/api/auth/telegram",
        json={
            "id": 555,
            "first_name": "Daniel",
            "auth_date": int(time.time()),
            "hash": "irrelevant",
        },
    )

    assert response.status_code == 500
    assert (
        response.json()["error"]["code"]
        == "TELEGRAM_AUTH_NOT_CONFIGURED"
    )

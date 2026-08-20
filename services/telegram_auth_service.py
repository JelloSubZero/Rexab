import hashlib
import hmac
import time


class TelegramAuthService:
    """
    Проверяет подпись данных от Telegram Login Widget.

    https://core.telegram.org/widgets/login#checking-authorization
    """

    MAX_AUTH_AGE_SECONDS = 24 * 60 * 60

    @staticmethod
    def verify(data: dict, bot_token: str) -> bool:
        received_hash = data.get("hash")

        if not received_hash:
            return False

        check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(data.items())
            if key != "hash" and value is not None
        )

        secret_key = hashlib.sha256(
            bot_token.encode("utf-8")
        ).digest()

        computed_hash = hmac.new(
            secret_key,
            check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            return False

        auth_date = data.get("auth_date")

        if auth_date is None:
            return False

        if time.time() - int(auth_date) > TelegramAuthService.MAX_AUTH_AGE_SECONDS:
            return False

        return True

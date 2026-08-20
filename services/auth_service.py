import time

import bcrypt
import jwt

from config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET


class AuthService:

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )

    @staticmethod
    def create_access_token(user_id: int) -> str:
        now = int(time.time())

        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + JWT_EXPIRE_MINUTES * 60,
        }

        return jwt.encode(
            payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )

    @staticmethod
    def decode_access_token(token: str) -> int | None:
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
            )
        except jwt.InvalidTokenError:
            return None

        try:
            return int(payload["sub"])
        except (KeyError, ValueError, TypeError):
            return None

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from jwt import InvalidTokenError

from backend.app.core.config import settings


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (TypeError, ValueError):
        return False


def create_access_token(*, subject: str, username: str, role_code: str) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    expires_in = settings.jwt_access_token_minutes * 60
    payload: dict[str, Any] = {
        "sub": subject,
        "username": username,
        "role_code": role_code,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise ValueError("Invalid or expired access token") from exc

    if payload.get("type") != "access" or not payload.get("sub"):
        raise ValueError("Invalid access token")
    return payload

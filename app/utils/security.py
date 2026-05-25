from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any

import bcrypt
from fastapi import HTTPException
from jose import jwt

from app.config import settings


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Le mot de passe ne doit pas dépasser 72 caractères."
        )

    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password.encode("utf-8")) > 72:
        return False

    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def create_access_token(subject: str, data: dict[str, Any] | None = None) -> str:
    payload = data.copy() if data else {}

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload.update({
        "sub": subject,
        "exp": expire
    })

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


def create_password_reset_token() -> str:
    return secrets.token_urlsafe(48)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def password_reset_expiry(minutes: int = 30) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)

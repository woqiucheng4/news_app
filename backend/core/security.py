"""
安全工具：密码哈希与 JWT 签发/解析。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from core.config import get_settings


def hash_password(password: str) -> str:
    digest = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return digest.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str,
    email: str,
    is_premium: bool = False,
    is_admin: bool = False,
    expires_delta: Optional[timedelta] = None,
) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.security.access_token_expire_minutes)
    )
    payload = {
        "sub": subject,
        "email": email,
        "is_premium": is_premium,
        "is_admin": is_admin,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.security.secret_key, algorithm=settings.security.algorithm)


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(days=settings.security.refresh_token_expire_days)
    )
    payload = {
        "sub": subject,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.security.secret_key, algorithm=settings.security.algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.security.secret_key, algorithms=[settings.security.algorithm])
        return payload
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

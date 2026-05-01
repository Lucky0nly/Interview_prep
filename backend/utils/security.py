from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Union

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_jwt_settings() -> Dict[str, Union[str, int]]:
    return {
        "secret_key": os.getenv("JWT_SECRET_KEY", "development-secret-key"),
        "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
        "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")),
    }


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: Union[str, int], expires_delta: Optional[timedelta] = None) -> str:
    settings = get_jwt_settings()
    expire_delta = expires_delta or timedelta(minutes=int(settings["access_token_expire_minutes"]))
    expire_at = datetime.now(timezone.utc) + expire_delta
    payload = {"sub": str(subject), "exp": expire_at}
    return jwt.encode(payload, settings["secret_key"], algorithm=settings["algorithm"])


def decode_access_token(token: str) -> dict:
    settings = get_jwt_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        return jwt.decode(token, settings["secret_key"], algorithms=[settings["algorithm"]])
    except JWTError as exc:
        raise credentials_exception from exc

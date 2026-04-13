import re

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.user import User
from backend.utils.security import create_access_token, decode_access_token, hash_password, verify_password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> str:
    normalized_email = email.strip().lower()
    if not EMAIL_PATTERN.match(normalized_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide a valid email address.")
    return normalized_email


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")
    if not any(character.isalpha() for character in password) or not any(character.isdigit() for character in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must include at least one letter and one number.",
        )
    return password


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = validate_email(email)
    return db.query(User).filter(User.email == normalized_email).first()


def register_user(db: Session, email: str, password: str) -> User:
    normalized_email = validate_email(email)
    validate_password_strength(password)

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists.")

    user = User(email=normalized_email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    normalized_email = validate_email(email)
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def build_auth_payload(user: User) -> dict:
    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "user": user,
    }


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User associated with token was not found.")

    return user

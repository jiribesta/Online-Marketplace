import uuid

import bcrypt
from fastapi import HTTPException
from sqlmodel import Session

from ..models import User

def check_unique_new_user(session: Session, new_user: User) -> None:
    existing_user = session.exec(select(User).where(or_(User.username == new_user.username, User.email == new_user.email))).first()

    if existing_user is None:
        return
    if existing_user.username == new_user.username:
        raise HTTPException(
            status=409,
            detail="Username already exists"
        )
    raise HTTPException(
        status=409,
        detail="Email already exists"
    )

def ensure_unique_user_id(session: Session, user: User) -> User:
    while session.get(User, user.id) is not None:
        user.id = uuid.uuid4()
    return user

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")

def get_user_by_id(sesison: Session, user_id: uuid.UUID) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status=404,
            detail="User not found"
        )
    return user

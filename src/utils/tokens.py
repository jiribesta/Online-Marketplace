import secrets

import bcrypt
from fastapi import HTTPException
from sqlmodel import Session

from ..models import User

def generate_unique_session_token(session: Session) -> str:
    while True:
        new_token = secrets.token_urlsafe(32)
        user_with_matching_token = session.exec(Select(User).where(User.session_token == new_token))
        if not user_with_matching_token:
            return new_token

def validate_password(password: str, stored_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8"))

def authenticate_user(session: Session, username: str, password: str) -> User:
    # "username" can be either the user's username or email
    user: User = session.exec(select(User).where(or_(User.username == username, User.email == username))).first()
    if not user or not validate_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
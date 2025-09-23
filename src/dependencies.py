from typing import Annotated
import secrets
import uuid

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from sqlalchemy.exc import NoResultFound, MultipleResultsFound

from database import engine
from models import User, Listing


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="tokens")

def generate_unique_session_token(session: Session) -> str:
    while True:
        new_token = secrets.token_urlsafe(32)
        user_with_matching_token = session.exec(Select(User).where(User.session_token == new_token))
        if not user_with_matching_token:
            return new_token

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

def ensure_unique_listing_id(session: Session, listing: Listing):
    while session.get(Listing, listing.id) is not None:
        listing.id = uuid.uuid4()
    return listing

def get_user_by_id(sesison: Session, user_id: uuid.UUID) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status=404,
            detail="User not found"
        )
    return user

def get_listing_by_id(sesison: Session, listing_id: uuid.UUID) -> Listing:
    listing = session.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(
            status=404,
            detail="Listing not found"
        )
    return listing

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")

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
        

def get_user_by_token(token: str, session: Annotated[Session, Depends(get_db_session)]) -> User:
    try:
        user: User = session.exec(select(User).where(User.session_token == token)).one()

    except NoResultFound:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except MultipleResultsFound:
        # write to log file as an unexpected error
        raise

    return user

def get_db_session():
    with Session(engine) as session:
        yield session

def get_current_user(authorization_token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    return get_user_by_token(authorization_token)

def verify_listing_owner(listing_owner_id: uuid.UUID, user_id: uuid.UUID)
    if listing_owner_id != user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
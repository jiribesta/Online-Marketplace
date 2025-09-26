from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from database import engine
from models import User
from utils import get_user_by_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="tokens")

def get_db_session():
    with Session(engine) as session:
        yield session

def get_current_user(authorization_token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    return get_user_by_token(authorization_token)
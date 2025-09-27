from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from .database import engine
from .models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="tokens")

def get_db_session():
    with Session(engine) as session:
        yield session

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

def get_current_user(authorization_token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    return get_user_by_token(authorization_token)
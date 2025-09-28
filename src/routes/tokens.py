from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from ..models import User
from ..utils.tokens import generate_unique_session_token, authenticate_user
from ..dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/tokens", tags=["tokens"])

obtain_session = Annotated[Session, Depends(get_db_session)]
get_logged_in_user = Annotated[User, Depends(get_current_user)]

@router.post("/")
async def login(session: obtain_session, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    authenticated_user = authenticate_user(session, form_data.username, form_data.password)

    if authenticated_user.session_token is not None:
        return authenticated_user.session_token

    new_token = generate_unique_session_token(session)

    authenticated_user.session_token = new_token
    session.add(authenticated_user)
    session.commit()

    return {"access_token": new_token, "token_type": "bearer"}

@router.delete("/")
async def logout(session: obtain_session, user: get_logged_in_user):
    user.session_token = None

    session.add(user)
    session.commit()

    return
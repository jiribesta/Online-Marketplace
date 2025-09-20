from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from models import User, UserCreate, UserGet, UserUpdate
from dependencies import get_db_session, oauth2_scheme, generate_unique_session_token, check_unique_new_user, hash_password, authenticate_user

router = APIRouter()

obtain_session: Annotated[Session, Depends(get_db_session)]

@router.post("/users", status_code=201, response_model=UserGet)
async def create_user(session: obtain_session, user: UserCreate, response: Response):
    new_hashed_password = hash_password(user.password)
    new_user = User.model_validate(user, update={"hashed_password": new_hashed_password})

    check_unique_new_user(session, new_user)

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    response.headers["Location"] = "/users/me"
    return new_user

@router.post("/token")
async def login(session: obtain_session, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    authenticated_user = authenticate_user(session, form_data.username, form_data.password)

    if authenticated_user.session_token is not None:
        return authenticated_user.session_token

    new_token = generate_unique_session_token(session)

    authenticated_user.session_token = new_token
    session.add(authenticated_user)
    session.commit()

    return {"access_token": new_token, "token_type": "bearer"}
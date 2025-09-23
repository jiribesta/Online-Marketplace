from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError

from models import User, UserCreate, UserGet, UserGetPublic, UserUpdate
from dependencies import get_db_session, oauth2_scheme, generate_unique_session_token, check_unique_new_user, ensure_unique_user_id, hash_password, authenticate_user, get_current_user

router = APIRouter()

obtain_session: Annotated[Session, Depends(get_db_session)]
get_logged_in_user: Annotated[User, Depends(get_current_user)]

@router.post("/users", status_code=201, response_model=UserGet)
async def create_user(session: obtain_session, user: UserCreate, response: Response):
    new_hashed_password = hash_password(user.password)
    new_user = User.model_validate(user, update={"hashed_password": new_hashed_password})

    check_unique_new_user(session, new_user)
    new_user = ensure_unique_user_id(session, new_user)

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    response.headers["Location"] = "/users/me"
    return new_user

@router.get("/users/me", response_model=UserGet)
async def get_user(user: get_logged_in_user):
    return user

@router.get("/users/{user_id}", response_model=UserGetPublic)
async def get_user_public(session: obtain_session):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status=404,
            detail="User not found"
        )
    return user

@router.patch("/users/me", response_model=UserGet)
async def update_user(session: obtain_session, user: get_logged_in_user, updated_user: UserUpdate):
    updated_data = updated_user.model_dump(exclude_unset=True)

    extra_data = {}
    if "password" in updated_data:
        new_password = updated_user["password"]
        new_hashed_password = hash_password(new_password)
        extra_data["hashed_password"] = new_hashed_password

    user.sqlmodel_update(updated_data, update=extra_data)

    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    # check for uniqueness violation
    except IntegrityError as excep:
        session.rollback()
        error_message = str(e.orig)
        if "UNIQUE constraint failed" in error_message:
            if "email" in error_message:
                raise HTTPException(status_code=400, detail="Email already exists")
            elif "username" in error_message:
                raise HTTPException(status_code=400, detail="Username already exists")
            else:
                raise HTTPException(status_code=400, detail="Unique constraint violation")
        raise # if the integrity error was somehow not related to uniqueness

    return user

@router.delete("/users/me", status_code=204)
async def delete_user(session: obtain_session, user: get_logged_in_user)
    session.delete(user)
    session.commit()

    return

@router.post("/tokens")
async def login(session: obtain_session, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    authenticated_user = authenticate_user(session, form_data.username, form_data.password)

    if authenticated_user.session_token is not None:
        return authenticated_user.session_token

    new_token = generate_unique_session_token(session)

    authenticated_user.session_token = new_token
    session.add(authenticated_user)
    session.commit()

    return {"access_token": new_token, "token_type": "bearer"}

@router.delete("/tokens", status_code=204)
async def logout(session: obtain_session, user: get_logged_in_user):
    user.session_token = None

    session.add(user)
    session.commit()

    return
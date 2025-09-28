from typing import Annotated
import uuid

from fastapi import APIRouter, HTTPException, Path, Header, Response, Depends, UploadFile, File
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError

from ..models import User, UserCreate, UserGetPrivate, UserGetPublicWithListings, UserUpdate
from ..utils import check_unique_new_user, ensure_unique_user_id, hash_password, get_user_by_id
from ..dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

obtain_session = Annotated[Session, Depends(get_db_session)]
get_logged_in_user = Annotated[User, Depends(get_current_user)]

@router.post("/", status_code=201, response_model=UserGetPrivate)
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

@router.get("/me", response_model=UserGetPrivate)
async def get_user(user: get_logged_in_user):
    return user

@router.get("/{user_id}", response_model=UserGetPublicWithListings)
async def get_user_public(session: obtain_session, user_id: Annotated[uuid.UUID, Path()]):
    return get_user_by_id(session, user_id)

@router.patch("/me", response_model=UserGetPrivate)
async def update_user(session: obtain_session, user: get_logged_in_user, updated_user: UserUpdate):
    updated_user_data = updated_user.model_dump(exclude_unset=True)

    extra_data = {}
    if "password" in updated_user_data:
        new_password = updated_user["password"]
        new_hashed_password = hash_password(new_password)
        extra_data["hashed_password"] = new_hashed_password

    user.sqlmodel_update(updated_user_data, update=extra_data)

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

@router.delete("/me", status_code=204)
async def delete_user(session: obtain_session, user: get_logged_in_user):
    session.delete(user)
    session.commit()

    return

@router.post("/me/picture")
async def upload_profile_picture(picture_file: Annotated[UploadFile, File()], content_lenght: Annotated[int, Header()]):
    pass
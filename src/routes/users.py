from typing import Annotated
import uuid

from fastapi import APIRouter, HTTPException, Path, Header, Response, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError

from ..app_config import PROFILE_PICTURE_MAX_SIZE, IMAGES_ENDPOINT, IMAGES_FOLDER_PATH
from ..logging_config import logger
from ..models import User, UserCreate, UserGetPrivate, UserGetPublicWithListings, UserUpdate
from ..utils.users import check_unique_new_user, ensure_unique_user_id, hash_password, get_user_by_id
from ..utils.images import ensure_unique_image_name, delete_profile_picture
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
            logger.info(f"Attempted patch to User model with non-unique data: {error_message}")
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

@router.post("/me/picture", status_code=201)
async def upload_profile_picture(
    session: obtain_session, 
    user: get_logged_in_user, 
    uploaded_file: Annotated[UploadFile, File()], 
    content_lenght: Annotated[int, Header()],
    response: Response
):
    if content_lenght > PROFILE_PICTURE_MAX_SIZE * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File size must not exceed {PROFILE_PICTURE_MAX_SIZE}MB")

    if uploaded_file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail="File type must be either JPEG or PNG")

    new_picture_name = ensure_unique_image_name(user.username)  # We want the filename to be username+uuid
    new_picture_path = os.path.join(IMAGES_FOLDER_PATH, new_picture_name)

    with open(new_picture_path, "wb") as new_picture:
        new_picture.write(await file.read())

    relative_path = f"{IMAGES_ENDPOINT}/{new_picture_name}"
    user.profile_picture_link = relative_path

    session.add(user)
    session.commit()

    response.headers["Location"] = relative_path
    return FileResponse(new_picture_path)

@router.put("/me/picture", status_code=201)
async def replace_profile_picture(
    *,
    session: obtain_session, 
    user: get_logged_in_user, 
    uploaded_file: Annotated[UploadFile | None, File()] = None, 
    content_lenght: Annotated[int | None, Header()] = None,
    response: Response
):
    if content_lenght is None or uploaded_file is None:
        delete_profile_picture(user)
        user.profile_picture_link = None
        
        session.add(user)
        session.commit()

        response.status_code = 204
        return
    
    if content_lenght > PROFILE_PICTURE_MAX_SIZE * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File size must not exceed {PROFILE_PICTURE_MAX_SIZE}MB")

    if uploaded_file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail="File type must be either JPEG or PNG")

    # If we've got a valid new picture, delete the old one first (if there is one)
    delete_profile_picture(user)

    new_picture_name = ensure_unique_image_name(user.username)  # We want the filename to be username+uuid
    new_picture_path = os.path.join(IMAGES_FOLDER_PATH, new_picture_name)

    with open(new_picture_path, "wb") as new_picture:
        new_picture.write(await file.read())

    relative_path = f"{IMAGES_ENDPOINT}/{new_picture_name}"
    user.profile_picture_link = relative_path

    session.add(user)
    session.commit()

    response.headers["Location"] = relative_path
    return FileResponse(new_picture_path)
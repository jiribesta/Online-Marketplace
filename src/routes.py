from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError

from models import User, UserCreate, UserGetPrivate, UserGetPublicWithListings, UserUpdate, ListingCategory, Listing, ListingCreate, ListingGet, ListingGetWithUser, ListingUpdate
from dependencies import get_db_session, oauth2_scheme, generate_unique_session_token, check_unique_new_user, ensure_unique_user_id, hash_password, authenticate_user, get_current_user, verify_listing_owner, get_user_by_id, get_listing_by_id

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

@router.get("/users/me", response_model=UserGetPrivate)
async def get_user(user: get_logged_in_user):
    return user

@router.get("/users/{user_id}", response_model=UserGetPublicWithListings)
async def get_user_public(session: obtain_session, user_id: Annotated[uuid.UUID, Path()]):
    return get_user_by_id(session, user_id)

@router.patch("/users/me", response_model=UserGet)
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

@router.delete("/users/me", status_code=204)
async def delete_user(session: obtain_session, user: get_logged_in_user):
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

@router.delete("/tokens")
async def logout(session: obtain_session, user: get_logged_in_user):
    user.session_token = None

    session.add(user)
    session.commit()

    return


@router.post("/listings", status_code=201, response_model=ListingGet)
async def create_listing(session: obtain_session, user: get_logged_in_user, listing: ListingCreate, response: Response):
    new_listing = Listing.model_validate(ListingCreate, update={"author_id" : user.id})

    new_listing = ensure_unique_listing_id(session, new_listing)

    session.add(new_listing)
    session.commit()
    session.refresh(new_listing)

    response.headers["Location"] = f"/listings/{new_listing.id}"
    return new_listing

@router.get("/listings", response_model=list[ListingGetWithUser])
async def query_listings(
    session: obtain_session, 
    offset: Annotated[int, Query(default=0, ge=0, lt=4294967296)],
    limit: Annotated[int, Query(default=32, gt=0, le=256)],
    category: Annotated[ListingCategory | None, Query(default=None)]
):
    if category is not None:
        query_statement = select(Listing).where(Listing.category == category).offset(offset).limit(limit)
    else:
        query_statement = select(Listing).offset(offset).limit(limit)

    listings = session.exec(query_statement).all()

    return listings

@router.get("/listings/{listing_id}", response_model=ListingGetWithUser)
async def get_listing(session: obtain_session, listing_id: Annotated[uuid.UUID, Path()]):
    return get_listing_by_id(session, listing_id)

@router.patch("/listings/{listing_id}", response_model=ListingGet)
async def update_listing(session: obtain_session, user: get_logged_in_user, listing_id: Annotated[uuid.UUID, Path()], updated_listing: ListingUpdate):
    listing = get_listing_by_id(session, listing_id)

    verify_listing_owner(listing.author_id, user.id)

    updated_listing_data = updated_listing.model_dump(exclude_unset=True)

    listing.sqlmodel_update(updated_listing_data)

    session.add(listing)
    session.commit()
    session.refresh(listing)

    return listing

@router.delete("/listings/{listing_id}", status_code=204)
async def delete_listing(session: obtain_session, user: get_logged_in_user, listing_id: Annotated[uuid.UUID, Path()]):
    listing = get_listing_by_id(session, listing_id)

    verify_listing_owner(listing.author_id, user.id)

    session.delete(listing)
    session.commit()

    return
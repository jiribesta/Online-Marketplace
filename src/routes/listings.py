from typing import Annotated
import uuid

from fastapi import APIRouter, Path, Query, Response, Depends
from sqlmodel import Session

from ..models import User, ListingCategory, Listing, ListingCreate, ListingGet, ListingGetWithUser, ListingUpdate
from ..utils import verify_listing_owner, get_listing_by_id
from ..dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/listings", tags=["listings"])

obtain_session = Annotated[Session, Depends(get_db_session)]
get_logged_in_user = Annotated[User, Depends(get_current_user)]

@router.post("/", status_code=201, response_model=ListingGet)
async def create_listing(session: obtain_session, user: get_logged_in_user, listing: ListingCreate, response: Response):
    new_listing = Listing.model_validate(ListingCreate, update={"author_id" : user.id})

    new_listing = ensure_unique_listing_id(session, new_listing)

    session.add(new_listing)
    session.commit()
    session.refresh(new_listing)

    response.headers["Location"] = f"/listings/{new_listing.id}"
    return new_listing

@router.get("/", response_model=list[ListingGetWithUser])
async def query_listings(
    session: obtain_session, 
    offset: Annotated[int, Query(ge=0, lt=4294967296)] = 0,
    limit: Annotated[int, Query(gt=0, le=256)] = 32,
    category: Annotated[ListingCategory | None, Query()] = None
):
    if category is not None:
        query_statement = select(Listing).where(Listing.category == category).offset(offset).limit(limit)
    else:
        query_statement = select(Listing).offset(offset).limit(limit)

    listings = session.exec(query_statement).all()

    return listings

@router.get("/{listing_id}", response_model=ListingGetWithUser)
async def get_listing(session: obtain_session, listing_id: Annotated[uuid.UUID, Path()]):
    return get_listing_by_id(session, listing_id)

@router.patch("/{listing_id}", response_model=ListingGet)
async def update_listing(session: obtain_session, user: get_logged_in_user, listing_id: Annotated[uuid.UUID, Path()], updated_listing: ListingUpdate):
    listing = get_listing_by_id(session, listing_id)

    verify_listing_owner(listing.author_id, user.id)

    updated_listing_data = updated_listing.model_dump(exclude_unset=True)

    listing.sqlmodel_update(updated_listing_data)

    session.add(listing)
    session.commit()
    session.refresh(listing)

    return listing

@router.delete("/{listing_id}", status_code=204)
async def delete_listing(session: obtain_session, user: get_logged_in_user, listing_id: Annotated[uuid.UUID, Path()]):
    listing = get_listing_by_id(session, listing_id)

    verify_listing_owner(listing.author_id, user.id)

    session.delete(listing)
    session.commit()

    return
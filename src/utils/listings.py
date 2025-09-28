import uuid

from fastapi import HTTPException
from sqlmodel import Session

from ..models import Listing

def verify_listing_owner(listing_owner_id: uuid.UUID, user_id: uuid.UUID):
    if listing_owner_id != user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_listing_by_id(sesison: Session, listing_id: uuid.UUID) -> Listing:
    listing = session.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(
            status=404,
            detail="Listing not found"
        )
    return listing

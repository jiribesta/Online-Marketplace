from fastapi import APIRouter

from . import users
from . import tokens
from . import listings

router = APIRouter()

router.include_router(users.router)
router.include_router(tokens.router)
router.include_router(listings.router)
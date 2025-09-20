from datetime import datetime, date, timezone
import uuid

from pydantic import EmailStr, field_validator
from sqlmodel import Field, Relationship, SQLModel

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, nullable=False)
    # only alphanumeric characters and underscores
    username: str = Field(unique=True, min_length=3, max_length=20, regex=r'^[a-zA-Z0-9_]+$', nullable=False)
    # only letters and spaces
    full_name: str | None = Field(default=None, min_length=1, max_length=100, regex=r'^[a-zA-Z\s]+$')
    birth_date: date = Field(nullable=False)
    postal_code: str = Field(min_length=4, max_length=10, nullable=False)
    # only letters and spaces
    city: str = Field(min_length=1, max_length=85, regex=r'^[a-zA-Z\s]+$', nullable=False)

    # check if birth_date is not in the future
    @field_validator("birth_date")
    def check_birth_date(cls, value):
        if value > datetime.date.today():
            raise ValueError("Birth date cannot be in the future")
        return value

class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(nullable=False)
    session_token: str | None = None
    signup_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    listings: list["Listing"] = Relationship(back_populates="author", cascade_delete=True)

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

    # check if password contains: an uppercase letter, a lowercase letter, a digit and a special character
    @field_validator('password')
    def check_password_complexity(cls, value):
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char in "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~" for char in value):
            raise ValueError("Password must contain at least one special character")
        return value

class UserGet(UserBase):
    id: uuid.UUID

class UserUpdate(SQLModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None
    full_name: str | None = None
    birth_date: date | None = None
    postal_code: str | None = None
    city: str | None = None


class ListingBase(SQLModel):
    author_id: uuid.UUID = Field(nullable=False, foreign_key="user.id", ondelete="CASCADE")
    title: str = Field(nullable=False)
    description: str | None = Field(default=None)
    price: float = Field(default=0, nullable=False)

class Listing(ListingBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    author: User = Relationship(back_populates="listings")

class ListingCreate(ListingBase):
    pass

class ListingGet(ListingBase):
    id: uuid.UUID

class ListingUpdate(ListingBase):
    title: str | None = None
    description: str | None = None
    price: float | None = None


#class Bookmark(SQLModel, table=True):
#    user_id: uuid.UUID = Field(primary_key=True, foreign_key=user.id)
#    listing_id: uuid.UUID = Field(primary_key=True, foreign_key=listing.id)
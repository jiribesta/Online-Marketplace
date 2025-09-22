from datetime import datetime, date, timezone
from enum import Enum
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
    session_token: str | None = Field(default=None, index=True)
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
    username: str | None = Field(default=None, min_length=3, max_length=20, regex=r'^[a-zA-Z0-9_]+$')
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, min_length=1, max_length=100, regex=r'^[a-zA-Z\s]+$')
    birth_date: date | None = None
    postal_code: str | None = Field(default=None, min_length=4, max_length=10)
    city: str | None = Field(default=None, min_length=1, max_length=85, regex=r'^[a-zA-Z\s]+$')

    @field_validator("birth_date")
    def check_birth_date(cls, value):
        if value > datetime.date.today():
            raise ValueError("Birth date cannot be in the future")
        return value

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

class ListingCategory(str, Enum):
    LAPTOPS = "laptops"
    DESKTOPS = "desktops"
    CONSOLES = "consoles"
    PC_ACCESSORIES = "pc accessories"
    PC_COMPONENTS = "pc components"
    SPARE_ELECTRONIC_PARTS = "spare electronic parts"
    SOFTWARE = "software"
    GAMES = "games"
    PHONES = "phones"
    PHONE_CASES = "phone cases"
    PHONE_ACCESSORIES = "phone accessories"
    SMART_WATCHES = "smart watches"
    TVS = "tvs"
    CAMERAS = "cameras"
    DRONES = "drones"
    BODY_CARE_DEVICES = "body care devices"
    HOME_APPLIANCES = "home appliances"
    OTHER_ELECTRONICS = "other electronics"
    CARS = "cars"
    CAR_ACCESSORIES = "car accessories"
    CAR_PARTS = "car parts"
    MOTORCYCLES = "motorcycles"
    MOTORCYCLE_PARTS = "motorcycle parts"
    INDOOR_FURNITURE = "indoor furniture"
    OUTDOOR_FURNITURE = "outdoor furniture"
    KITCHENWARE = "kitchenware"
    TOOLS = "tools"
    SMART_HOME_ELECTRONICS = "smart home electronics"
    BUILDING_MATERIALS = "building materials"
    ANIMALS = "animals"
    BIKES = "bikes"
    FISHING_TOOLS = "fishing tools"
    FISHING_SUPPLIES = "fishing supplies"
    OUTDOOR_AND_HIKING_EQUIPMENT = "outdoor and hiking equipment"
    WORKOUT_EQUIPMENT = "workout equipment"
    WATER_SPORTS_EQUIPMENT = "water sports equipment"
    WINTER_SPORTS_EQUIPMENT = "winter sports equipment"
    OTHER_SPORTS_EQUIPMENT = "other sports equipment"
    BOARD_GAMES = "board games"
    CARD_GAMES = "card games"
    PARTY_GAMES = "party games"
    PUZZLES = "puzzles"
    SETS = "sets"
    FILMS = "films"
    MUSIC = "music"
    MUSICAL INSTRUMENTS = "musical instruments"
    MUSIC EQUIPMENT = "music equipment"
    BOOKS = "books"
    MAGAZINES = "magazines"
    COMICS = "comics"
    TEXTBOOKS = "textbooks"
    MAPS_AND_GUIDES = "maps and guides"
    OTHER_PRINTED_MEDIA = "other printed media"
    MENS_CLOTHING = "men's clothing"
    WOMENS_CLOTHING = "women's clothing"
    UNDERWEAR = "underwear"
    BAGS = "bags"
    HANDBAGS = "handbags"
    FASHION_ACCESSORIES = "fashion accessories"
    MENS_SHOES = "men's shoes"
    WOMENS_SHOES = "women's shoes"
    JEWELRY = "jewelry"
    WRISTWATCHES = "whistwatches"
    MEDICAL_SUPPLIES = "medical supplies"
    COLLECTIBLES = "collectibles"
    OTHER = "other"

class ListingBase(SQLModel):
    author_id: uuid.UUID = Field(nullable=False, foreign_key="user.id", ondelete="CASCADE")
    title: str = Field(nullable=False)
    description: str | None = Field(default=None)
    category: ListingCategory = Field(nullable=False)
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
    category: ListingCategory | None = None
    price: float | None = None


#class Bookmark(SQLModel, table=True):
#    user_id: uuid.UUID = Field(primary_key=True, foreign_key=user.id)
#    listing_id: uuid.UUID = Field(primary_key=True, foreign_key=listing.id)
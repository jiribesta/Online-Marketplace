from sqlmodel import create_engine

from config import DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

DB_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DB_URL, echo=True)
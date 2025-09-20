from sqlmodel import create_engine

DB_URL = "postgresql://user:password@localhost:port/dbname"

engine = create_engine(DB_URL, echo=True)
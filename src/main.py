from contextlib import asynccontextmanager

from fastapi import FastAPI

from models import SQLModel
from routes import router

# Manage startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router)
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.logging_config import logger
from src.database import engine
from src.models import SQLModel  # So we can then .create_all() DB objects
from src.routes.router_aggregate import router

# Manage startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        logger.exception("Unexpected exception when creating DB tables: %s", e)
        raise
    logger.info("Application startup successful")
    
    yield

    logger.info("Application shutdown sucessful")

app = FastAPI(lifespan=lifespan)
app.include_router(router)
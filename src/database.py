from sqlmodel import create_engine

from .logging_config import logger
from .app_config import DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

DB_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DB_URL, echo=True)
except Exception as e:
    logger.exception("Unexpected exception when creating DB engine: %s", e)
    raise
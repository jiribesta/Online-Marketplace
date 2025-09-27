import logging

from .app_config import LOG_FILE_PATH

logger = logging.getLogger("main")

logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(LOG_FILE_PATH)
console_handler = logging.StreamHandler()

file_handler.setLevel(logging.DEBUG)  # Log all messages to the file
console_handler.setLevel(logging.WARNING)  # Log warnings and worse to the console

file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_formatter = logging.Formatter('%(levelname)s - %(message)s')

file_handler.setFormatter(file_formatter)
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
import os
import uuid

from ..app_config import IMAGES_FOLDER_PATH


def ensure_unique_image_name(uuidless_image_name: str) -> str:
    new_image_name = f"{old_image_name}_{uuid.uuid4()}"

    while os.path.exists(os.path.join(IMAGES_FOLDER_PATH, new_image_name)):
        new_image_name = f"{old_image_name}_{uuid.uuid4()}"

    return new_image_name
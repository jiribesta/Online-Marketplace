import os
import uuid

from ..app_config import IMAGES_ENDPOINT, IMAGES_FOLDER_PATH
from ..logging_config import logger
from ..models import User


def ensure_unique_image_name(uuidless_image_name: str) -> str:
    new_image_name = f"{old_image_name}_{uuid.uuid4()}"

    while os.path.exists(os.path.join(IMAGES_FOLDER_PATH, new_image_name)):
        new_image_name = f"{old_image_name}_{uuid.uuid4()}"

    return new_image_name

def delete_profile_picture(user: User):
    if user.profile_picture_link is not None:
        picture_name = user.profile_picture_link.split('/')[-1]
        try:
            os.delete(os.path.join(IMAGES_FOLDER_PATH, picture_name))
        except Exception as e:
            logger.exception(f"Unexpected exception when deleting profile picture: {e}")
            raise
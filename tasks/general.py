from utils.logging import warning

from constants.general import (
    DATA_FOLDER,
    AVATAR_FOLDER,
    DEFAULT_AVATAR
)

async def ensure_paths() -> None:
    for path in (DATA_FOLDER, AVATAR_FOLDER):
        if not path.exists(): path.mkdir(parents=True)

    if not DEFAULT_AVATAR.exists(): warning("Default avatar (.data/avatars/default.png) file does not exist, there will be no default avatar!")
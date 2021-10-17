from utils.logging import warning

from constants.general import (
    DATA_FOLDER,
    AVATAR_FOLDER,
    DEFAULT_AVATAR,
    SCREENSHOT_FOLDER,
    MAPS_FOLDER,
    VANILLA_REPLAY_PATH,
    RELAX_REPLAY_PATH,
    AUTOPILOT_REPLAY_PATH,
)

async def ensure_paths() -> None:
    for path in (
        DATA_FOLDER, AVATAR_FOLDER, SCREENSHOT_FOLDER, MAPS_FOLDER,
        VANILLA_REPLAY_PATH, RELAX_REPLAY_PATH, AUTOPILOT_REPLAY_PATH
    ):
        if not path.exists(): path.mkdir(parents=True)

    if not DEFAULT_AVATAR.exists(): warning("Default avatar (.data/avatars/default.png) file does not exist, there will be no default avatar!")
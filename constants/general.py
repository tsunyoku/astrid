from pathlib import Path

from objects import glob

BASE_WEB_MESSAGE = (
    f'astrid.\n'
    'the most efficient python osu! server.\n\n'
    'online players:\n'
)

WELCOME_MSG = (
    f"Welcome to astrid. We have a [{glob.config.discord_server} Discord server] if you require any help.\nEnjoy!"
)

RESTRICTED_MSG = (
    f"Your account is currently in restricted mode. If you require assistance, please join our [{glob.config.discord_server} Discord]!"
)

FROZEN_MSG = (
    "Your account is currently frozen. If you do not provide a liveplay within the next 7 days, your account will be restricted!\n"
    f"You can join our Discord [{glob.config.discord_server} here]"
)

DATA_FOLDER = Path.cwd() / ".data"
AVATAR_FOLDER = DATA_FOLDER / "avatars"
DEFAULT_AVATAR = AVATAR_FOLDER / "default.png"
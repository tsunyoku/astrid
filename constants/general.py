from pathlib import Path

from objects import glob

import string

BASE_WEB_MESSAGE = (
    "astrid.\n"
    "the most efficient python osu! server.\n\n"
    "online players:\n"
)

WELCOME_MSG = f"Welcome to astrid. We have a [{glob.config.discord_server} Discord server] if you require any help.\nEnjoy!"
RESTRICTED_MSG = f"Your account is currently in restricted mode. If you require assistance, please join our [{glob.config.discord_server} Discord]!"

FROZEN_MSG = (
    "Your account is currently frozen. If you do not provide a liveplay within the next 7 days, your account will be restricted!\n"
    f"You can join our Discord [{glob.config.discord_server} here]"
)

LOG_BASE = "Handled {req.type} request on {url} in {req.elapsed} ({req.code})"

LEADERBOARD_BASE = (
    "SELECT s.*, s.{sort} sort, u.name FROM {table} s "
    "INNER JOIN users u on s.uid = u.id "
    "WHERE {where_args} ORDER BY {sort} DESC LIMIT 100"
)

PB_BASE = (
    "SELECT s.*, s.{sort} sort, u.name FROM {table} s "
    "INNER JOIN users u on s.uid = u.id "
    "WHERE {where_args} ORDER BY {sort} DESC LIMIT 1"
)

PB_COUNT = (
    "SELECT COUNT(*) + 1 FROM {table} s "
    "INNER JOIN users u on s.uid = u.id "
    "WHERE {where_args} ORDER BY {sort} DESC"
)

COUNT_QUERY = (
    "SELECT COUNT(*) FROM {table} s INNER JOIN users u on "
    "s.userid = u.id WHERE {where_args}"
)

BEATMAP_API_URL = "https://old.ppy.sh/api/get_beatmaps"
UNSUB_HEADER = b"-1|false"

BASE_HEADER = (
    "{map.status.value}|false|{map.id}|{map.sid}|{count}\n"
    "0\n{map.full_name}\n0"
)

CHIMU_V1 = "chimu.moe/v1" in glob.config.beatmap_mirror_url

DATA_FOLDER = Path.cwd() / ".data"
AVATAR_FOLDER = DATA_FOLDER / "avatars"
SCREENSHOT_FOLDER = DATA_FOLDER / "screenshots"
DEFAULT_AVATAR = AVATAR_FOLDER / "default.png"

RANDOM_CHOICE = string.ascii_uppercase + string.ascii_lowercase + string.digits
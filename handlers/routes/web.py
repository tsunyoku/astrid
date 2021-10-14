from collections import defaultdict
from xevel import Router, Request
from typing import Union

from constants.general import LOG_BASE, SCREENSHOT_FOLDER, UNSUB_HEADER, CHIMU_V1
from utils.general import random_string, string_get, body_get
from handlers.leaderboards import fetch_leaderboard
from utils.password import hash_md5, generate_password
from utils.general import now_float, now, make_safe
from utils.logging import debug, info
from packets.writer import userStats
from objects.beatmap import Beatmap
from constants.modes import lbModes
from constants.mods import Mods
from objects import glob

web_router = Router(f"osu.{glob.config.serving_domain}")

def check_auth(name: str, password_md5: str, request: Request) -> bool:
    name = name.replace('%20', ' ') # fun

    if not (player := glob.players.get_from_login(name, password_md5)):
        debug(f"{name} failed authentication")
        return False

    request.extras['player'] = player
    return True

@web_router.after_request()
async def log_request(request: Request) -> Request:
    stripped_url = "/" + "/".join(request.url.split('/')[1:]) # removes domain
    msg = LOG_BASE.format(req=request, url=stripped_url)

    if (player := request.extras.get('player')) and request.code < 400: msg += f" | Request by {player.name}"
    debug(msg)

    return request

@web_router.route("/web/osu-screenshot.php", ["POST"])
async def upload_screenshot(request: Request) -> bytes:
    args = request.args
    files = request.files

    if not check_auth(args['u'], args['p'], request): return b"error: pass"
    if not (screenshot := files.get('ss')): return b"missing screenshot"

    if screenshot[:4] == b'\xff\xd8\xff\xe0' and screenshot[6:11] == b'JFIF\x00': ext = ".jpg"
    else: ext = ".png"

    screenshot_name = random_string(8) + ext
    screenshot_path = SCREENSHOT_FOLDER / screenshot_name
    screenshot_path.write_bytes(screenshot)

    return screenshot_name.encode()

@web_router.route("/ss/<screenshot_name>")
async def get_screenshot(request: Request, screenshot_name: int) -> bytes:
    screenshot = SCREENSHOT_FOLDER / screenshot_name

    if not screenshot.exists(): return b"screenshot not found"

    screenshot_extension = screenshot_name.split('.')[1]
    request.resp_headers['Content-Type'] = f'image/{screenshot_extension}'

    return screenshot.read_bytes()

@web_router.route("/web/bancho_connect.php")
async def bancho_connect(request: Request) -> bytes:
    # I want to add ingame verification here, however it requires a frontend placement to make it fully work -
    # so I'm not sure what I will do for now.

    return b"owo"

@web_router.route("/web/osu-getfriends.php")
async def get_friends_list(request: Request) -> bytes:
    if not check_auth(request.args['u'], request.args['h'], request): return b''

    return '\n'.join(
        map(str, request.extras["player"].friends)
    ).encode()

@web_router.route("/web/osu-getseasonal.php")
async def get_seasonal_backgrounds(request: Request) -> list: return glob.config.seasonal_backgrounds

@web_router.route("/d/<map_id>")
async def download_map(request: Request, map_id: str) -> tuple[int, bytes]:
    map_id = map_id.removesuffix("n")
    no_vid = 1 if ("n" == map_id[-1]) else 0

    url = "https://{glob.config.beatmap_mirror_url}/d/{map_id}"
    if CHIMU_V1: url = f"https://{glob.config.beatmap_mirror_url}/download/{map_id}?n={no_vid}"

    request.resp_headers["Location"] = url
    return (301, b"")

# NOTE: I believe this to be the best way to make search set and search (osu!direct), 
# however I may provide alternate options for those who do not want to mirror Bancho

@web_router.route("/web/osu-search-set.php")
async def search_set(request: Request) -> bytes:
    args = request.args
    if not check_auth(args['u'], args['h'], request): return b"error: pass"

    args |= {
        "u": glob.config.bancho_username,
        "h": glob.config.bancho_password
    }

    return (await string_get("https://old.ppy.sh/web/osu-search-set.php", args)).encode()

@web_router.route("/web/osu-search.php")
async def search_set(request: Request) -> dict:
    args = request.args
    if not check_auth(args['u'], args['h'], request): return b"error: pass"

    args |= {
        "u": glob.config.bancho_username,
        "h": glob.config.bancho_password
    }

    req = await string_get("https://old.ppy.sh/web/osu-search.php", args)
    return req

@web_router.route("/users", ["POST"])
async def ingame_registration(request: Request) -> Union[dict, bytes]:
    start = now_float()
    args = request.args

    # still hating this setup osu!!!
    name = args["user[username]"].strip()
    email = args["user[user_email]"].strip()
    raw_password = args["user[password]"].strip()

    errors = defaultdict(list) # very convenient
    if not args.get("check") or not all ((name, email, raw_password)): return b"missing required parameters"
    if " " in name and "_" in name: errors["username"] += "Username cannot contain a space and an underscore!"
    if await glob.sql.fetchval("SELECT 1 FROM users WHERE name = %s", [name]): errors["username"] += "Username already taken!"
    if await glob.db.fetchval("SELECT 1 FROM users WHERE email = %s", [email]): errors["user_email"] += "Email already in use!"
    if not len(raw_password) >= 8: errors["password"] += "Password must be 8 characters or longer!" # may do extra validation on the password
    if errors: return {"form_error": {"user": errors}}

    if int(args["check"]) == 0:
        encrypted_password = generate_password(hash_md5(raw_password))

        user_id = await glob.sql.execute(
            "INSERT INTO users (name, email, pw, safe_name, registered_at) VALUES "
            "(%s, %s, %s, %s, %s)",
            [name, email, encrypted_password, make_safe(name), now()]
        )

        await glob.sql.execute("INSERT INTO stats (id) VALUES (%s)", [user_id])

        elapsed = (now_float() - start) * 1000
        info(f'{name} registered (Time Elapsed: {elapsed:.2f}ms)')

    return b"ok"

# NOTE: As above with osu!direct, I feel this is the best way to get accurate results, but may provide alternatives later.

@web_router.route("/web/osu-getbeatmapinfo.php")
async def map_info(request: Request) -> bytes:
    args = request.args
    if not check_auth(args['u'], args['h'], request): return b"error: pass"

    args |= {
        "u": glob.config.bancho_username,
        "h": glob.config.bancho_password
    }

    return (await body_get("https://old.ppy.sh/web/osu-getbeatmapinfo.php", args, request.body)).encode()

@web_router.route("/web/check-updates.php")
async def client_updates(request: Request) -> bytes:
    args = request.args

    args |= {
        "u": glob.config.bancho_username,
        "h": glob.config.bancho_password
    }

    return (await string_get("https://old.ppy.sh/web/check-updates.php", args)).encode()

@web_router.route("/web/osu-osz2-getscores.php")
async def map_leaderboards(request: Request) -> bytes:
    args = request.args
    if not check_auth(args['us'], args['ha'], request): return b"error: pass"

    player = request.extras["player"]
    map_md5 = args["c"]
    mods = Mods(int(args['mods']))
    mode = lbModes(int(args["m"]), mods.value)
    leaderboard_mode = int(args["v"])

    if glob.unsubmitted_cache.get(map_md5): return UNSUB_HEADER

    # update player info cus yea
    if mode != player.mode or mods != player.mods:
        player.mode = mode
        player.mods = mods

        if not player.restricted: glob.players.enqueue(userStats(player))

    if not (map := await Beatmap.from_md5(map_md5)):
        # TODO: check if it is unsubmitted or needs updating
        glob.unsubmitted_cache.add(map_md5, map)
        return UNSUB_HEADER

    # TODO: check against next check and check map status
    if not map.has_leaderboard: return f"{map.status}|false".encode()
    return await fetch_leaderboard(map, player, leaderboard_mode)

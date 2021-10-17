from collections import defaultdict
from xevel import Router, Request
from typing import Union

from constants.general import LOG_BASE, SCREENSHOT_FOLDER, UNSUB_HEADER, CHIMU_V1
from utils.general import random_string, string_get, body_get, pair_panel
from utils.password import hash_md5, generate_password
from constants.statuses import scoreStatus, mapStatus
from handlers.leaderboards import fetch_leaderboard
from utils.general import now_float, now, make_safe
from constants.privileges import Privileges
from utils.logging import debug, info
from packets.writer import userStats
from objects.beatmap import Beatmap
from constants.modes import Mode
from objects.score import Score
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
    if await glob.sql.fetchval("SELECT 1 FROM users WHERE email = %s", [email]): errors["user_email"] += "Email already in use!"
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
    mode = Mode.from_lb(int(args["m"]), mods.value)
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

@web_router.route("/web/osu-submit-modular-selector.php", ["POST"])
async def score_sub(request: Request) -> bytes:
    args, headers = request.args, request.headers

    score = await Score.from_score_submission(args)
    
    if not score: return b"error: no" # error within score sub process
    elif not score.user: return b"" # user isn't online, empty response will cause resubmit attempts
    elif not score.map: return b"error: beatmap" # unsubmitted/invalid map
    elif score.mods & Mods.UNRANKED: return b"error: no"

    if score.mode != score.user.mode or score.mods != score.user.mods:
        score.user.mode = score.mode
        score.user.mods = score.mods

        if not score.user.restricted: glob.players.enqueue(userStats(score.user))

    if not (token := headers.get('Token')) and not glob.config.custom_clients or token == "": await score.user.restrict("Circumventing anticheat")
    if headers.get('User-Agent') != "osu!": await score.user.restrict("Score submitter")
    if await glob.sql.fetchval(f'SELECT 1 FROM {score.mode.table} WHERE checksum = %s', [score.checksum]): return b"error: no" # duplicate score

    elapsed = args['st' if score.passed else 'ft']
    if not elapsed or not elapsed.isdecimal():
        await score.user.flag('Old/edited client (missing time elapsed)')
        return b"error: no"

    if score.map.gives_pp and not (
        score.user.priv & Privileges.Whitelisted or score.user.restricted
    ): # pp cap if the map gives pp and they cant bypass the cap (and also are not restricted)
        pp_cap = 1000000000

        if score.pp >= pp_cap: await score.user.restrict(f"Exceeding {score.mode!r} pp cap ({score.pp:,.0f}pp) on {score.map.full_name} +{score.mods!r}")

    await score.submit() # we are isolating this function because it needs to do stuff like clear leaderboards

    if score.status != scoreStatus.Failed:
        replay = request.files.get('score')
        if not replay or replay == b"\r\n":
            await score.user.restrict("No replay sent upon score submission")
            return "error: ban" # in this case we cannot let submission run ahead

        replay_path = score.mode.replay_path / f"{score.id}.osr"
        replay_path.write_bytes(replay)

    stats = score.user.current_stats
    old_stats = stats.copy()
    
    stats.pc += 1 # playcount
    stats.tscore += score.score
    additive = score.score
    if score.previous_score: additive -= int(score.previous_score.score)

    if score.passed and score.map.has_leaderboard:
        if score.map.status == mapStatus.Ranked: stats.rscore += additive
        if stats.max_combo < score.combo: stats.max_combo = score.combo

        if score.status == scoreStatus.Best and score.pp: await score.user.recalc_stats()

    await score.user.update_stats()

    panels = []
    achievements = []

    if score.passed and score.map.has_leaderboard:
        for achievement in glob.achievements:
            if achievement in score.user.achievements: continue

            if achievement.cond(score):
                await score.user.unlock_achievement(achievement)
                achievements.append(repr(achievement))

    panels.append(
        f"beatmapId:{score.map.id}|"
        f"beatmapSetId:{score.map.sid}|"
        f"beatmapPlaycount:{score.map.plays}|"
        f"beatmapPasscount:{score.map.passes}|"
        f"approvedDate:{score.map.formatted_update}"
    )

    if score.map.has_leaderboard:
        panels.append("|".join((
            "chartId:beatmap",
            f"chartUrl:{score.map.set_url}",
            "chartName:Beatmap Ranking",

            *((
                pair_panel("rank", score.previous_score.rank, score.rank),
                pair_panel("rankedScore", score.previous_score.score, score.score),
                pair_panel("maxCombo", score.previous_score.combo, score.combo),
                pair_panel("accuracy", round(score.previous_score.acc, 2), round(score.acc, 2)),
                pair_panel("pp", score.previous_score.pp, score.pp)
            ) if score.previous_score else (
                pair_panel("rank", None, score.rank),
                pair_panel("rankedScore", None, score.score),
                pair_panel("maxCombo", None, score.combo),
                pair_panel("accuracy", None, round(score.acc, 2)),
                pair_panel("pp", None, score.pp)
            )),

            f"onlineScoreId:{score.id}"
        )))

    panels.append("|".join((
        "chartId:overall",
        f"chartUrl:https://{glob.config.serving_domain}/u/{score.user.id}",
        "chartName:Global Ranking",

        *((
            pair_panel("rank", old_stats.rank, stats.rank),
            pair_panel("rankedScore", old_stats.rscore, stats.rscore),
            pair_panel("totalScore", old_stats.tscore, stats.tscore),
            pair_panel("maxCombo", old_stats.max_combo, stats.max_combo),
            pair_panel("accuracy", round(old_stats.acc, 2), round(stats.acc, 2)),
            pair_panel("pp", round(old_stats.pp), round(stats.pp))
        ) if old_stats else (
            pair_panel("rank", None, stats.rank),
            pair_panel("rankedScore", None, stats.rscore),
            pair_panel("totalScore", None, stats.tscore),
            pair_panel("maxCombo", None, stats.max_combo),
            pair_panel("accuracy", None, round(stats.acc, 2)),
            pair_panel("pp", None, round(stats.pp))
        )),

        f"achievements-new:{'/'.join(achievements)}",
    )))

    # TODO: add announcements

    score.user.last_score = score
    info(f"[{score.mode!r}] {score.user.name} submitted a {score.pp:,.0f}pp score on {score.map.full_name} ({score.status.name})")
    return "\n".join(panels).encode()

@web_router.route("/difficulty-rating", ["POST"])
async def starRatingRoute(request: Request) -> tuple: # STUPID peppy
    request.resp_headers["Location"] = "https://osu.ppy.sh/difficulty-rating"
    return (301, b"")

    
    

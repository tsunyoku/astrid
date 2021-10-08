from xevel import Router, Request

from constants.general import LOG_BASE, SCREENSHOT_FOLDER
from utils.general import random_string
from utils.logging import debug
from objects import glob

web_router = Router(f"osu.{glob.config.serving_domain}")

def check_auth(name: str, password_md5: str, request: Request) -> bool:
    name = name.replace('%20', ' ') # fun

    if not (player := glob.players.get_from_login(name, password_md5)):
        debug(f"{name} failed authentication")
        return False

    request.extras['player'] = player

@web_router.after_request()
async def log_request(request: Request) -> Request:
    stripped_url = "/" + '/'.join(request.url.split('/')[1:]) # removes domain
    msg = LOG_BASE.format(req=request, url=stripped_url)

    if (player := request.extras.get('player')): msg += f" | Request by {player.name}"
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
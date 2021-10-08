from xevel import Router, Request

from utils.logging import debug
from objects import glob

web_router = Router(f"osu.{glob.config.serving_domain}")

LOG_BASE = (
    "{{code}} | Handled {{type}} request on {{url}} in {{elapsed}}"
)

async def check_auth(name: str, password_md5: str, request: Request) -> bool:
    name = name.replace('%20', ' ') # fun

    if not (player := glob.players.get_from_login(name, password_md5)):
        debug(f"{name} failed authentication")
        return False

    request.extras['player'] = player

@web_router.after_request()
async def log_request(request: Request) -> Request:
    msg = LOG_BASE
    if (player := request.extras.get('player')): msg += f" | Request by {player.name}"

    debug(msg)
    return request
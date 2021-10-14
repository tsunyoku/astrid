from xevel import Router, Request

from constants.general import AVATAR_FOLDER, DEFAULT_AVATAR
from objects import glob

avatar_router = Router(
    f'a.{glob.config.serving_domain}',
)

@avatar_router.route("/<user_id>")
async def get_avatar(request: Request, user_id: int) -> bytes:
    request.resp_headers["Content-Type"] = "image/png"

    if (avatar := AVATAR_FOLDER / f"{user_id}.png").exists(): return avatar.read_bytes()
    if DEFAULT_AVATAR.exists(): return DEFAULT_AVATAR.read_bytes()

    return b"" # should never really occur
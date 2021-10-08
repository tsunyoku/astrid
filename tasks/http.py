from aiohttp import ClientSession

from utils.logging import debug
from objects import glob

async def create_http_session() -> None:
    glob.http = ClientSession()

    debug("HTTP client session created!")

async def close_http_session() -> None:
    if glob.http: await glob.http.close()

    debug("HTTP client session closed!")
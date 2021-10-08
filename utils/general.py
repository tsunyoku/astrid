from typing import Callable

from constants.general import RANDOM_CHOICE
from objects import glob

import pymysql
import random
import time

def now() -> int: return int(time.time())
def now_float() -> float: return time.time()
def make_safe(username: str) -> str: return username.lower().replace(' ', '_')
def escape_enum(val, _ = None) -> str: return str(int(val))
def random_string(length: int) -> str: return random.choices(RANDOM_CHOICE, k=length)

def pymysql_encode(conv: Callable) -> Callable:
    def wrapper(cls):
        pymysql.converters.encoders[cls] = conv
        return cls

    return wrapper

async def json_get(url: str, args: dict) -> dict:
    request = await glob.http.get(url, params=args)
    if request.status != 200: return {}

    return await request.json()

async def string_get(url: str, args: dict) -> str:
    request = await glob.http.get(url, params=args)
    if request.status != 200: return ""

    return await request.text()

async def body_get(url: str, args: dict, body: bytes) -> str:
    request = await glob.http.get(url, params=args, data=body)
    if request.status != 200: return ""

    return await request.text()
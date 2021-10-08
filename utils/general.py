from typing import Callable

from constants.general import RANDOM_CHOICE

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
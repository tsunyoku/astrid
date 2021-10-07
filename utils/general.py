from typing import Callable

import pymysql
import time

def now() -> int: return int(time.time())
def now_float() -> float: return time.time()
def make_safe(username: str) -> str: return username.lower().replace(' ', '_')
def escape_enum(val, _ = None) -> str: return str(int(val))

def pymysql_encode(conv: Callable) -> Callable:
    def wrapper(cls):
        pymysql.converters.encoders[cls] = conv
        return cls

    return wrapper
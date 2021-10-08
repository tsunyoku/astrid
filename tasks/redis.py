from utils.logging import debug
from objects import glob

import aioredis

async def connect_redis() -> None: # TODO: port to aioredis rewrite
    glob.redis = await aioredis.create_redis_pool(
        f"redis://{glob.config.redis['host']}",
        db=glob.config.redis['db'],
        password=glob.config.redis['password'] or None
    )

    debug("Redis connected!")

async def disconnect_redis() -> None:
    if glob.redis:
        glob.redis.close()
        await glob.redis.wait_closed()

    debug("Redis disconnected!")
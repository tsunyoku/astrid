#!/usr/bin/env python3.9

# third-party imports
from xevel import Xevel

# tasks
from tasks.sql import (
    connect_sql, 
    disconnect_sql
)

from tasks.redis import (
    connect_redis, 
    disconnect_redis
)

from tasks.http import (
    create_http_session, 
    close_http_session
)

from tasks.general import ensure_paths

# routers
from handlers.avatars import avatar_router
from handlers.bancho import bancho_router
from handlers.web import web_router

# caching
from caching.caches import initialise_cache

# internal imports
from utils.logging import info
from objects import glob

# third-party imports
import asyncio
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
app = Xevel(glob.config.serving_socket, loop=asyncio.get_event_loop(), gzip=4)

STARTUP_TASKS = (
    connect_sql,
    connect_redis,
    create_http_session,
    ensure_paths,
)

SHUTDOWN_TASKS = (
    disconnect_sql,
    disconnect_redis,
    close_http_session,
)

ROUTERS = (
    bancho_router,
    avatar_router,
    web_router,
)

@app.before_serving()
async def startup() -> None: 
    for task in STARTUP_TASKS: await task()
    app.add_task(initialise_cache) # avoid blocking startup for something that isn't needed

    info("astrid started!")

@app.after_serving()
async def shutdown() -> None:
    for task in SHUTDOWN_TASKS: await task()
    info("astrid stopped!")

if __name__ == '__main__':
    for router in ROUTERS: app.add_router(router)
    app.start()
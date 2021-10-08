from fatFuckSQL import fatFawkSQL

from utils.logging import debug
from objects import glob

async def connect_sql() -> None: 
    glob.sql = await fatFawkSQL.connect(**glob.config.sql)
    debug("SQL connected!")

async def disconnect_sql() -> None: 
    if glob.sql: await glob.sql.close()
    debug("SQL disconnected!")
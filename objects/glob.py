import config # indirect import

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fatFuckSQL import fatFawkSQL
    from aiohttp import ClientSession
    from aioredis import Redis

    from caching.password import PasswordCache
    from caching.channel import ChannelCache
    from caching.user import UserCache
    from caching.clan import ClanCache
    from objects.player import Player
    from caching.cache import Cache

sql: 'fatFawkSQL' = None
redis: 'Redis' = None
http: 'ClientSession' = None
players: 'UserCache' = None
channels: 'ChannelCache' = None
clans: 'ClanCache' = None
password_cache: 'PasswordCache' = None
geoloc_cache: 'Cache' = None
bot: 'Player' = None
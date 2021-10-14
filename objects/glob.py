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

http: "ClientSession" = None
sql: "fatFawkSQL" = None
redis: "Redis" = None

channels: "ChannelCache" = None
leaderboards: "Cache" = None
achievements: "Cache" = None
players: "UserCache" = None
clans: "ClanCache" = None
maps: "Cache" = None

bot: "Player" = None

password_cache: "PasswordCache" = None
unsubmitted_cache: "Cache" = None
geoloc_cache: "Cache" = None
pb_cache: "Cache" = None

restricted_packets = {}
packets = {}

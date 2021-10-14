from typing import Any

from .achievement import AchievementCache
from constants.modes import osuModes
from .password import PasswordCache
from objects.player import Player
from .channel import ChannelCache
from constants.mods import Mods
from .user import UserCache
from .clan import ClanCache
from .cache import Cache
from objects import glob

glob.players = UserCache()
glob.password_cache = PasswordCache()
glob.geoloc_cache = Cache()
glob.channels = ChannelCache()
glob.clans = ClanCache()
glob.achievements = AchievementCache()
glob.leaderboards = Cache()  # format of identifier: (map md5, mode)
glob.maps = Cache()  # format of identifiers: (md5 or beatmap id, mode if beatmap id)
glob.unsubmitted_cache = Cache()
glob.pb_cache = Cache()

async def initialise_cache() -> None: # loaded in order of priority
    await glob.channels.load_channels()
    await glob.clans.load_clans()

    await glob.players.load_players()
    await glob.achievements.load_achievements()

def get_lb_cache(
    mode: osuModes, md5: str, lb_type: int, 
    mods: Mods = None, user: Player = None
) -> Any:
    """Stupidly cursed function to try and make leaderboard cache efficient and clean."""

    lb_base = glob.leaderboards.get((mode, md5))
    if not lb_base: 
        glob.leaderboards.add((mode, md5,), Cache()) # empty for now
        lb_base = glob.leaderboards.get((mode, md5))

    if lb_type == 1: cache_identifier = 1
    elif lb_type == 2: cache_identifier = (2, mods,)
    elif lb_type == 3: cache_identifier = (3, user,)
    elif lb_type == 4: cache_identifier = (4, user.country_iso.lower(),)

    return lb_base.get(cache_identifier)

def add_lb_cache(
    mode: osuModes, md5: str, 
    lb_type: int, lb_scores: list, lb_count: int,
    mods: Mods = None, user: Player = None
) -> None:
    """Stupidly cursed function to update or add to leaderboard cache of any type."""

    lb_base = glob.leaderboards.get((mode, md5))
    if not lb_base: 
        glob.leaderboards.add((mode, md5,), Cache()) # empty for now
        lb_base = glob.leaderboards.get((mode, md5))

    if lb_type == 1: cache_identifier = 1
    elif lb_type == 2: cache_identifier = (2, mods,)
    elif lb_type == 3: cache_identifier = (3, user,)
    elif lb_type == 4: cache_identifier = (4, user.country_iso.lower(),)

    lb_base.add(cache_identifier, (lb_scores, lb_count,))

def get_pb_cache(
    mode: osuModes, md5: str, lb_type: int, 
    mods: Mods = None, user: Player = None
) -> Any:
    """Stupidly cursed function to try and make personal best cache efficient and clean."""

    lb_base = glob.pb_cache.get((mode, md5, user))
    if not lb_base: 
        glob.pb_cache.add((mode, md5, user), Cache()) # empty for now
        lb_base = glob.pb_cache.get((mode, md5, user))

    if lb_type == 1: cache_identifier = 1
    elif lb_type == 2: cache_identifier = (2, mods,)
    elif lb_type == 3: cache_identifier = 3
    elif lb_type == 4: cache_identifier = (4, user.country_iso.lower(),)

    return lb_base.get(cache_identifier)

def add_pb_cache(
    mode: osuModes, md5: str, 
    lb_type: int, pb_score: dict, pb_place: int,
    mods: Mods = None, user: Player = None
) -> None:
    """Stupidly cursed function to update or add to leaderboard cache of any type."""

    lb_base = glob.pb_cache.get((mode, md5, user))
    if not lb_base: 
        glob.pb_cache.add((mode, md5, user), Cache()) # empty for now
        lb_base = glob.pb_cache.get((mode, md5, user))

    if lb_type == 1: cache_identifier = 1
    elif lb_type == 2: cache_identifier = (2, mods,)
    elif lb_type == 3: cache_identifier = 3
    elif lb_type == 4: cache_identifier = (4, user.country_iso.lower(),)

    lb_base.add(cache_identifier, (pb_score, pb_place,))
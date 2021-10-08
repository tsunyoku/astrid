from .achievement import AchievementCache
from .password import PasswordCache
from .channel import ChannelCache
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

async def initialise_cache() -> None: # loaded in order of priority
    await glob.channels.load_channels()
    await glob.clans.load_clans()

    await glob.players.load_players()
    await glob.achievements.load_achievements()
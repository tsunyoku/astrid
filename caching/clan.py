from typing import Optional, Union

from objects.channel import Channel
from utils.logging import debug
from objects.clan import Clan
from objects import glob

class ClanCache:
    def __init__(self) -> None:
        self.name_cache: dict = {}

    @property
    def clans(self) -> list[Clan]: return self.name_cache.values()

    def __iter__(self) -> list[Clan]: return iter(self.clans)
    def __contains__(self, clan: Clan) -> bool: return clan in self.clans

    async def load_clans(self) -> None:
        """Loads all clans into cache"""

        clans = await glob.sql.fetch('SELECT * FROM clans')
        for clan in clans: await self.add_clan(clan, sql=True)

        debug("Cached all clans!")

    async def add_clan(self, clan: Union[dict, Clan], sql: bool = False) -> None:
        if sql: clan = Clan(**clan)
        self.name_cache |= {clan.name: clan}

        clan.channel = Channel(
            name='#clan',
            descr=f'Clan chat for clan {clan.name}',
            auto=True,
            perm=True
        )

        clan.country = await glob.sql.fetchval('SELECT country FROM users WHERE id = %s', [clan.owner])

    def get(self, **kwargs) -> Optional[Clan]:
        for _type in ('id', 'name'):
            if (clan := kwargs.pop(_type, None)): clan_type = _type; break
        else: return

        for _clan in self.name_cache.values():
            if getattr(_clan, clan_type) == clan: return _clan

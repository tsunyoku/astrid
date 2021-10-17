from typing import Optional, Union

from constants.countries import country_codes
from constants.privileges import Privileges
from objects.player import Player
from utils.logging import debug
from objects import glob

class UserCache:
    def __init__(self) -> None:
        self._cache: list = []

    async def load_players(self) -> None:
        """Loads all players into cache"""

        players = await glob.sql.fetch('SELECT * FROM users')
        for player in players: 
            if player not in self._cache: await self.add_player(player, sql=True)

        debug("Cached all players!")

    async def add_player(self, player: Union[dict, Player], sql: bool = False) -> None:
        if sql:
            player['country_iso'] = player['country'].upper()
            player['country'] = country_codes.get(player['country_iso'])
            player = await Player.login(player)
            await player.set_stats()

        if player.id == 1: glob.bot = player; glob.bot.online = True

        self._cache.append(player)

    @property
    def online(self) -> list: return [u for u in self._cache if u.online]

    @property
    def unrestricted(self) -> list: return [u for u in self.online if not u.disallowed]

    def enqueue(self, data: bytes) -> None:
        for user in self.online: user.enqueue(data)

    def get(self, **kwargs) -> Optional[Player]:
        for _type in ('id', 'name', 'token', 'safe_name'):
            if (player := kwargs.pop(_type, None)): player_type = _type; break
        else: return

        for u in self._cache:
            if getattr(u, player_type) == player:
                if kwargs.get("online", True) and not u.online: return

                return u

    def get_from_login(self, name: str, password_md5: str) -> Optional[Player]:
        if not (user := self.get(name=name)): return
        if user.password_md5 == password_md5: return user
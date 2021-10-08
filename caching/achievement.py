from typing import Optional, Union

from objects.achievement import Achievement
from utils.logging import debug
from objects import glob

class AchievementCache:
    def __init__(self) -> None:
        self.name_cache: dict = {}
        self.id_cache: dict = {}

    @property
    def achievements(self) -> list[Achievement]: return self.name_cache.values()

    def __iter__(self) -> list[Achievement]: return iter(self.achievements)
    def __contains__(self, achievement: Achievement) -> bool: return achievement in self.achievements

    async def load_achievements(self) -> None:
        """Loads all achievements into cache"""

        achievements = await glob.sql.fetch('SELECT * FROM achievements')
        for achievement in achievements: self.add_achievement(achievement, sql=True)

        debug("Cached all achievements!")

    def add_achievement(self, achievement: Union[dict, Achievement], sql: bool = False) -> None:
        if sql: achievement = Achievement(**achievement)

        self.name_cache |= {achievement.name: achievement}
        self.id_cache |= {achievement.id: achievement}

    def get(self, _achievement: Union[str, int]) -> Optional[Achievement]:
        if isinstance(_achievement, int): cache = self.id_cache
        elif isinstance(_achievement, str): cache = self.name_cache

        if (achievement := cache.get(_achievement)): return achievement
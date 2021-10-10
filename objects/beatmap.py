from datetime import datetime
from typing import Optional

from constants.general import BEATMAP_API_URL
from constants.statuses import mapStatuses
from utils.general import now, json_get
from constants.modes import osuModes
from . import glob

class Beatmap:
    def __init__(self, **kwargs) -> None:
        self.md5: str = kwargs.get("md5", "")
        self.id: int = kwargs.get("id", 0)
        self.sid: int = kwargs.get("sid", 0)
        self.bpm: float = kwargs.get("bpm", 0.0)
        self.cs: float = kwargs.get("cs", 0.0)
        self.ar: float = kwargs.get("ar", 0.0)
        self.od: float = kwargs.get("od", 0.0)
        self.hp: float = kwargs.get("hp", 0.0)
        self.sr: float = kwargs.get("sr", 0.00)
        self.mode: "osuModes" = osuModes(kwargs.get("mode", 0))
        self.artist: str = kwargs.get("artist", "")
        self.title: str = kwargs.get("title", "")
        self.diff: str = kwargs.get("diff", "")
        self.mapper: str = kwargs.get("mapper", "")
        self.status: "mapStatuses" = mapStatuses(kwargs.get("status", 0))
        self.frozen: bool = kwargs.get("frozen", 0) == 1
        self.update: int = kwargs.get("update", 0)
        self.nc: int = kwargs.get("nc", 0)  # next api status check
        self.plays: int = kwargs.get("plays", 0)
        self.passes: int = kwargs.get("passes", 0)

    @property
    def full_name(self) -> str: return f"{self.artist} - {self.title} [{self.diff}]"

    @property
    def url(self) -> str: return f"https://osu.{glob.config.serving_domain}/beatmaps/{self.id}"

    @property
    def set_url(self) -> str: return f"https://osu.{glob.config.serving_domain}/beatmapsets/{self.sid}"

    @property
    def embed(self) -> str: return f"[{self.url} {self.name}]"

    @classmethod
    async def from_md5(cls, md5: str) -> Optional["Beatmap"]:
        """
        Attempts to grab a beatmap by its md5 hash.

        Arguments:
            - md5 (str) - The md5 hash to check for

        First it will attempt to grab the md5 from our beatmaps cache
        If it is not in cache, we try the database
        Finally if it is not in the database, we try the api
        If it still isn't found, the map is invalid (unsubmitted/needs updating)

        Returns:
            - Beatmap object, if the map is found
        """

        if self := glob.maps.get(md5): return self
        if self := await cls.fetch_md5_from_sql(md5): return self
        if self := await cls.fetch_md5_from_api(md5): return self

    @classmethod
    async def fetch_md5_from_sql(cls, md5: str) -> Optional["Beatmap"]:
        """
        Attempts to grab a beatmap from the database by its md5 hash.

        Arguments:
            - md5 (str) - The md5 hash to check for

        Returns:
            - Beatmap object, if the map is found
        """

        map_row = await glob.sql.fetchrow("SELECT * FROM maps WHERE md5 = %s", [md5])
        if not map_row: return

        self = cls(**map_row)
        glob.maps.add(md5, self)  # add to cache for future use

        return self

    @classmethod
    async def fetch_md5_from_api(cls, md5: str) -> Optional["Beatmap"]:
        """
        Attempts to grab a beatmap from osu!api (v1) by its md5 hash.

        Arguments:
            - md5 (str) - The md5 hash to check for

        Returns:
            - Beatmap object, if the map is found
        """

        map_json = await json_get(BEATMAP_API_URL, {"k": glob.config.bancho_api_key, "h": md5})
        if not map_json: return

        map_info = map_json[0]
        self = cls(
            id=int(map_info["beatmap_id"]),
            sid=int(map_info["beatmapset_id"]),
            md5=md5,
            bpm=float(map_info["bpm"]),
            cs=float(map_info["diff_size"]),
            ar=float(map_info["diff_approach"]),
            od=float(map_info["diff_overall"]),
            hp=float(map_info["diff_drain"]),
            sr=float(map_info["difficultyrating"]),
            mode=osuModes(int(map_info["mode"])),
            artist=map_info["artist"],
            title=map_info["title"],
            diff=map_info["version"],
            mapper=map_info["creator"],
            status=mapStatuses.from_api(int(map_info["approved"])),
            update=datetime.strptime(map_info["last_update"], "%Y-%m-%d %H:%M:%S").timestamp(),
            nc=now(),
        )

        glob.maps.add(md5, self) # add to cache for future use
        await self.save_to_db()

        return self

    async def save_to_db(self) -> None:
        """Inserts or updates a beatmap object into the database"""

        await glob.sql.execute(
            "REPLACE INTO maps (id, sid, md5, bpm, cs, ar, od, hp, sr, mode, "
            "artist, title, diff, mapper, status, frozen, `update`, nc, plays, passes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            self.__dict__.values(), # haha!
        )

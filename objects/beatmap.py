from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from constants.general import BEATMAP_API_URL
from constants.statuses import mapStatus
from utils.general import now, json_get
from constants.modes import Mode
from . import glob

@dataclass
class Beatmap:
    """Dataclass to represent a single beatmap, alongside helper functions"""

    id: int
    sid: int
    md5: str
    bpm: float
    cs: float
    ar: float
    od: float
    hp: float
    sr: float
    mode: "Mode"
    artist: str
    title: str
    diff: str
    mapper: str
    status: "mapStatus"
    frozen: bool
    update: int
    nc: int # next api status check
    plays: int
    passes: int

    @property
    def full_name(self) -> str: return f"{self.artist} - {self.title} [{self.diff}]"

    @property
    def url(self) -> str: return f"https://osu.{glob.config.serving_domain}/beatmaps/{self.id}"

    @property
    def set_url(self) -> str: return f"https://osu.{glob.config.serving_domain}/beatmapsets/{self.sid}"

    @property
    def embed(self) -> str: return f"[{self.url} {self.full_name}]"

    @property
    def has_leaderboard(self) -> bool: return self.status >= mapStatus.Ranked

    @property
    def gives_pp(self) -> bool: return self.has_leaderboard and self.status != mapStatus.Loved

    @property
    def formatted_update(self) -> str: return datetime.utcfromtimestamp(self.update).strftime("%Y-%m-%d %H:%M:%S")

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

        if map_row.get("server"): del map_row["server"] # iteki tings

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
            mode=Mode(int(map_info["mode"])),
            artist=map_info["artist"],
            title=map_info["title"],
            diff=map_info["version"],
            mapper=map_info["creator"],
            status=mapStatus.from_api(int(map_info["approved"])),
            update=datetime.strptime(map_info["last_update"], "%Y-%m-%d %H:%M:%S").timestamp(),
            nc=now(),
            frozen=False,
            plays=0,
            passes=0,
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
            list(self.__dict__.values()) # haha!
        )

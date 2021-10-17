from py3rijndael import RijndaelCbc, ZeroPadding
from typing import Optional

from caching.caches import clear_lb_cache, clear_pb_cache
from constants.privileges import Privileges
from constants.statuses import scoreStatus
from constants.general import PB_COUNT
from constants.flags import osuFlags
from utils.logging import warning
from constants.modes import Mode
from constants.mods import Mods
from utils.pp import PPUtils
from .beatmap import Beatmap
from .player import Player
from . import glob

import base64
import time

class Score:
    """
    Class to represent a single score, 
    and handle the procesing of one from the database or upon score submission
    """

    def __init__(self):
        self.id: Optional[int] = None
        self.map: Optional[Beatmap] = None
        self.user: Optional[Player] = None

        self.score: Optional[int] = None
        self.acc: Optional[float] = None
        self.n300: Optional[int] = None
        self.n100: Optional[int] = None
        self.n50: Optional[int] = None
        self.miss: Optional[int] = None
        self.geki: Optional[int] = None
        self.katu: Optional[int] = None
        self.grade: Optional[str] = None
        self.mods: Optional[Mods] = None
        self.readable_mods: Optional[str] = None
        self.combo: Optional[int] = None
        self.mode: Optional[Mode] = None

        self.rank: Optional[int] = None
        self.pp: Optional[float] = None
        self.sr: Optional[float] = None # star rating

        self.fc: Optional[bool] = None
        self.passed: Optional[bool] = None
        self.status: Optional[scoreStatus] = None
        self.time: Optional[int] = None

        self.osuver: int = None
        self.checksum: str = None # used to check for duplicates
        self.flags: osuFlags = None # 2016 anticheat, not really that useful
        self.previous_score: "Score" = None
        
        # not sure if i will actually include these yet
        #ur: float = 0
        #frametime: float = 0

    @classmethod
    async def from_score_submission(cls, args: list) -> 'Score':
        """Creates a Score object from an osu! score submission request"""

        aes = RijndaelCbc(
            key="osu!-scoreburgr---------" + args['osuver'],
            iv=base64.b64decode(args['iv']),
            padding=ZeroPadding(32),
            block_size=32
        )

        data = aes.decrypt(base64.b64decode(args['score'])).decode().split(":")
        score = cls()

        score.user = glob.players.get_from_login(data[1].rstrip(), args['pass'])
        score.map = await Beatmap.from_md5(data[0])
        if not score.user or not score.map: return score

        if len(data) != 18: return warning(f"Received an invalid score submission from {score.user.name}")

        score.checksum = data[2]

        if not all(
            map(str.isdecimal, data[3:11] + [data[13], data[15], data[16]])
        ): return warning(f"Received an invalid score submission from {score.user.name}")

        (   
            score.n300, score.n100, score.n50,
            score.geki, score.katu, score.miss,
            score.score, score.combo
        ) = map(int, data[3:11])

        score.fc = data[11] == "True"
        score.passed = data[14] == "True"
        score.grade = data[12] if score.passed else "F"

        score.mods = Mods(int(data[13]))
        score.readable_mods = repr(score.mods)
        score.mode = Mode.from_lb(int(data[15]), score.mods)

        score.time = int(time.time())
        score.flags = osuFlags(data[17].count(" ") & ~4) # 2016 peppy really thought he was slick huh

        score.calc_accuracy()
        await score.calc_pp()

        if score.passed: 
            await score.calc_status()
            if not score.user.restricted and score.map.has_leaderboard: await score.calc_rank()
        else: score.status = scoreStatus.Failed

        return score

    @classmethod
    async def from_sql(cls, sql_row: dict) -> "Score":
        score = cls()

        score.id = sql_row['id']
        score.map = await Beatmap.from_md5(sql_row['md5'])
        if not score.map: return # ?

        score.user = glob.players.get(id=sql_row['uid'])
        if not score.user: return score

        score.pp = sql_row['pp']
        score.score = sql_row['score']
        score.combo = sql_row['combo']
        score.mods = Mods(sql_row['mods'])
        score.acc = sql_row['acc']
        score.n300 = sql_row['n300']
        score.n100 = sql_row['n100']
        score.n50 = sql_row['n50']
        score.miss = sql_row['miss']
        score.geki = sql_row['geki']
        score.katu = sql_row['katu']
        score.grade = sql_row['grade']
        score.fc = sql_row['fc']
        score.status = scoreStatus(sql_row['status'])
        score.mode = Mode.from_lb(sql_row['mode'], score.mods)

        score.time = sql_row['time']
        score.passed = score.status.value != 0

        if not score.user.restricted and score.map.has_leaderboard: score.rank = await score.calc_rank()
        else: score.rank = 0

        return score

    def calc_accuracy(self) -> None:
        mode = self.mode.as_vn

        if mode == 0:
            hits = self.n300 + self.n100 + self.n50 + self.miss

            if hits == 0:
                self.acc = 0.0
                return
            else:
                self.acc = 100.0 * (
                        (self.n50 * 50.0) +
                        (self.n100 * 100.0) +
                        (self.n300 * 300.0)
                ) / (hits * 300.0)
        elif mode == 1:
            hits = self.n300 + self.n100 + self.miss

            if hits == 0:
                self.acc = 0.0
                return
            else:
                self.acc = 100.0 * ((self.n100 * 0.5) + self.n300) / hits
        elif mode == 2:
            hits = self.n300 + self.n100 + self.n50 + self.katu + self.miss

            if hits == 0:
                self.acc = 0.0
                return
            else:
                self.acc = 100.0 * (self.n300 + self.n100 + self.n50) / hits
        elif mode == 3:
            hits = self.n300 + self.n100 + self.n50 + self.geki + self.katu + self.miss

            if hits == 0:
                self.acc = 0.0
                return
            else:
                self.acc = 100.0 * (
                        (self.n50 * 50.0) +
                        (self.n100 * 100.0) +
                        (self.katu * 200.0) +
                        ((self.n300 + self.geki) * 300.0)
                ) / (hits * 300.0)

    async def calc_pp(self) -> None:
        if self.mode.value < 4: calc = PPUtils.calc_peace(self) # use peace pp, we only want to use oppai for rx/ap scores
        else: calc = PPUtils.calc_oppai(self)

        self.pp, self.sr = await calc.calculate()

    async def calc_status(self) -> None:
        if (last_score := self.user.last_score) and last_score.map == self.map: # we'll check last score first just for efficiency, maybe we are lucky!
                if self.pp > last_score.pp or (self.pp == last_score.pp and self.score > last_score.score): # higher pp, or same pp but higher score
                    self.status = scoreStatus.Best
                    last_score.status = scoreStatus.Submitted
                else:
                    self.status = scoreStatus.Submitted
        else: # try db, it wasnt their last score
            previous_score = await glob.sql.fetchrow(
                f'SELECT * FROM {self.mode.table} WHERE uid = %s AND md5 = %s AND mode = %s AND status = 2',
                [self.user.id, self.map.md5, self.mode.as_vn]
            )

            if previous_score: 
                self.previous_score = await Score.from_sql(previous_score)

                if self.pp > float(self.previous_score.pp) \
                or (self.pp == float(self.previous_score.pp) and self.score > int(self.previous_score.score)): # higher pp, or same pp but higher score
                    self.status = scoreStatus.Best
                    self.previous_score.status = scoreStatus.Submitted
                    await glob.sql.execute(f'UPDATE {self.mode.table} SET status = 1 WHERE id = %s', [self.previous_score.id])
                else: self.status = scoreStatus.Submitted
            else:
                self.status = scoreStatus.Best

    async def calc_rank(self) -> None:
        place_args = " AND ".join((
            "s.md5 = %s",
            "s.mode = %s",
            "s.status = 2",
            f"s.pp > %s",
            f"NOT u.priv & {Privileges.Disallowed}"
        ))

        place_vals = (
            self.map.md5,
            self.user.mode.as_vn,
            self.pp
        )
        
        pb_query = PB_COUNT.format(
            sort=self.user.mode.sort,
            table=self.user.mode.table,
            where_args=place_args
        )

        self.rank = int(await glob.sql.fetchval(pb_query, place_vals))

    async def submit(self) -> None:
        if self.status == scoreStatus.Best:
            clear_lb_cache(self.mode, self.map.md5) # clear lb cache so scores are correct
            clear_pb_cache(self.mode, self.map.md5, self.user) # clear lb cache for same reason

            self.map.passes += 1

        self.map.plays += 1

        await glob.sql.execute(f"UPDATE maps SET passes = %s, plays = %s WHERE md5 = %s", [self.map.passes, self.map.plays, self.map.md5])

        self.id = await glob.sql.execute(
            f'INSERT INTO {self.mode.table} (md5, score, acc, pp, combo, mods, n300, '
            f'geki, n100, katu, n50, miss, grade, status, mode, time, uid, readable_mods, fc, osuver, checksum, flags) VALUES '
            f'(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            [self.map.md5, self.score, self.acc, self.pp, self.combo, self.mods, self.n300,
            self.geki, self.n100, self.katu, self.n50, self.miss, self.grade, self.status.value, 
            self.mode.as_vn, self.time, self.user.id, self.readable_mods, self.fc, self.osuver, self.checksum, self.flags.value]
        )


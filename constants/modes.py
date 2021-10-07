from functools import cache
from enum import Enum

from utils.general import pymysql_encode, escape_enum
from .mods import Mods

m_str = (
    'osu!std',
    'osu!taiko',
    'osu!catch',
    'osu!mania',

    'std!rx',
    'taiko!rx',
    'catch!rx',
    'std!ap',
    
    8, # placeholder
    9, # placeholder v2

    'osu!std cheat',
    'osu!taiko cheat',
    'osu!catch cheat',
    'osu!mania cheat',

    'std!rx cheat',
    'taiko!rx cheat',
    'catch!rx cheat',
    'std!ap cheat'
)

@pymysql_encode(escape_enum)
class osuModes(Enum):
    std = 0
    taiko = 1
    catch = 2
    mania = 3

    std_rx = 4
    taiko_rx = 5
    catch_rx = 6
    std_ap = 7

    std_cheat = 10
    taiko_cheat = 11
    catch_cheat = 12
    mania_cheat = 13

    std_rx_cheat = 14
    taiko_rx_cheat = 15
    catch_rx_cheat = 16
    std_ap_cheat = 17
    

    def __repr__(self) -> str:
        return m_str[self.value]

    @property
    @cache
    def table(self) -> str:
        if self.value < 10:
            if self.value in (4, 5, 6):
                return 'scores_rx'
            elif self.value in (0, 1, 2, 3):
                return 'scores'
            else:
                return 'scores_ap'
        else:
            if self.value in (14, 15, 16):
                return 'scores_rx_cheat'
            elif self.value in (10, 11, 12, 13):
                return 'scores_cheat'
            else:
                return 'scores_ap_cheat'

    @property
    @cache
    def as_vn(self) -> int:
        if self.value < 10:
            if self.value in (0, 4, 7):
                return 0
            elif self.value in (1, 5):
                return 1
            elif self.value in (2, 6):
                return 2
            else:
                return self.value
        else:
            if self.value in (10, 14, 17):
                return 0
            elif self.value in (11, 15):
                return 1
            elif self.value in (12, 16):
                return 2
            elif self.value == 13:
                return 3

    @property
    @cache
    def sort(self) -> str:
        if self.value > 7: val = 13
        else: val = 3

        if self.value > val:
            return 'pp'
        else:
            return 'score'

    @property
    @cache
    def leaderboard(self) -> str:
        if self.value < 10:
            if self.value in (4, 5, 6):
                return 'lb_rx'
            elif self.value in (0, 1, 2, 3):
                return 'lb'
            else:
                return 'lb_ap'
        else:
            if self.value in (14, 15, 16):
                return 'lb_rx_cheat'
            elif self.value in (10, 11, 12, 13):
                return 'lb_cheat'
            else:
                return 'lb_ap_cheat'

def lbModes(mode: int, mods: int, cheat: bool = False) -> osuModes:
    if cheat: add = 10
    else: add = 0

    if mods & Mods.RELAX:
        if mode == 3:
            return osuModes(3 + add) # XD cursed way of doing nothing if it isnt cheat

        return osuModes((mode + 4) + add)
    elif mods & Mods.AUTOPILOT:
        if mode != 0:
            return osuModes(mode + add)

        return osuModes(7 + add)

    return osuModes(mode + add)
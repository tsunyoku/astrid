from peace_performance_python.objects import Beatmap, Calculator
from cmyui.osu.oppai_ng import OppaiWrapper
from pathlib import Path

from constants.general import MAPS_FOLDER
from .general import string_get

import math

class PeaceCalculator: # wrapper around peace performance for ease of use
    def __init__(self, score) -> None:
        self.score = score
        self.map = score.map

    def calculate(self, map_path: str) -> tuple[float]:
        beatmap = Beatmap(map_path)
        calculator = Calculator(
            acc=self.score.acc,
            miss=self.score.miss,
            katu=self.score.katu,
            score=self.score.score,
            combo=self.score.combo,
            mode=self.score.mode.as_vn,
            mods=self.score.mods.value,
        )

        result = calculator.calculate(beatmap)
        return (result.pp, result.stars)

class OppaiCalculator: # wrapper around oppaiwrapper for ease of use
    def __init__(self, score) -> None:
        self.score = score
        self.map = score.map

    def calculate(self, map_path: str) -> tuple[float]:
        with OppaiWrapper("oppai-ng/liboppai.so") as calculator:
            calculator.configure(
                mode=self.score.mode.as_vn,
                acc=self.score.acc,
                mods=self.score.mods.value,
                combo=self.score.combo,
                nmiss=self.score.miss
            )

            calculator.calculate(map_path)

            pp, sr = calculator.get_pp(), calculator.get_sr()
            return (pp, sr)

class PPUtils:
    def __init__(self, score, calc) -> None:
        self.score = score
        self.map = score.map

        self.calc: object = calc

    @classmethod
    def calc_peace(cls, score) -> 'PPUtils':
        self = cls(
            score=score,
            calc=PeaceCalculator
        )

        return self

    @classmethod
    def calc_oppai(cls, score) -> 'PPUtils':
        self = cls(
            score=score,
            calc=OppaiCalculator
        )

        return self

    async def calculate(self) -> tuple[float]:
        map_path = MAPS_FOLDER / f"{self.map.id}.osu"
        if not map_path.exists():
            map_file = await string_get(f"https://old.ppy.sh/osu/{self.map.id}")
            map_path.write_bytes(map_file.encode())

        pp, sr = self.calc(self.score).calculate(map_path)

        if pp in (math.inf, math.nan): return (0.0, 0.0)
        return (pp, sr)
from dataclasses import dataclass
from typing import Callable

@dataclass
class Achievement:
    """Dataclass to represent a single achievement"""

    id: int
    image: str
    name: str
    descr: str
    cond: Callable
    custom: bool

    def __repr__(self) -> str: return f"{self.image}+{self.name}+{self.desc}"
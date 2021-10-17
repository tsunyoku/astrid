from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .channel import Channel
#     from .match import Match

@dataclass
class Clan:
    """Dataclass to represent a single clan"""

    id: int
    name: str
    tag: str
    owner: int
    channel: Optional['Channel'] = None
    members: list = field(default_factory=lambda: [])

    #battle: Match
    score: int = 0
    country: str = ""

    #rank: int
    #country_rank: int
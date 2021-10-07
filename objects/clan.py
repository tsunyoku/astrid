from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .channel import Channel
#     from .match import Match

class Clan:
    def __init__(self, **kwargs) -> None:
        self.id: int = kwargs.get('id', 0)
        self.name: str = kwargs.get('name', 0)
        self.tag: str = kwargs.get('tag', 0)
        self.owner: int = kwargs.get('owner', 0)
        self.channel: Optional[Channel] = None
        self.members: list = []

        #self.battle: Match = None
        self.score: int = kwargs.get('score', 0)
        self.country: str = None

        #self.rank: int = 0
        #self.country_rank: int = 0
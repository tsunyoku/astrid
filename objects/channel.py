from typing import TYPE_CHECKING

from packets import writer
from objects import glob

if TYPE_CHECKING: from .player import Player

class Channel:
    def __init__(self, **kwargs):
        self.name: str = kwargs.get('name')
        self.desc: str = kwargs.get('desc')
        self.auto_join: bool = kwargs.get('auto', False)
        self.permanent_channel: bool = kwargs.get('perm', False)

        self.players: list['Player'] = []

    @property
    def player_count(self) -> int: return len(self.players)

    def send(self, sent_by: 'Player', msg: str, send_to_self: bool = False) -> None:
        if not send_to_self: 
            self.enqueue(
                writer.sendMessage(
                    sent_by.name,
                    msg,
                    self.name,
                    sent_by.id
                ),
                ignore_list = [sent_by]
            )
        else:
            self.enqueue(
                writer.sendMessage(
                    sent_by.name,
                    msg,
                    self.name,
                    sent_by.id
                )
            )

    def enqueue(self, data: bytes, ignore_list: list['Player'] = []) -> None:
        for u in self.players:
            if u not in ignore_list: u.enqueue(data)

    def add(self, user: 'Player') -> None: self.players.append(user)

    def remove(self, user: 'Player') -> None:
        self.players.remove(user)
        if len(self) == 0 and not self.permanent_channel: glob.channels.remove(self)

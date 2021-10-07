from typing import Optional, Union

from objects.channel import Channel
from utils.logging import debug
from objects import glob

class ChannelCache:
    def __init__(self) -> None:
        self.name_cache: dict = {}

    @property
    def channels(self) -> list[Channel]: return self.name_cache.values()

    def __iter__(self) -> list[Channel]: return iter(self.channels)
    def __contains__(self, channel: Channel) -> bool: return channel in self.channels

    async def load_channels(self) -> None:
        """Loads all channels into cache"""

        channels = await glob.sql.fetch('SELECT * FROM channels')
        for channel in channels: self.add_channel(channel, sql=True)

        debug("Cached all channels!")

    def add_channel(self, channel: Union[dict, Channel], sql: bool = False) -> None:
        if sql: channel = Channel(**channel)
        self.name_cache |= {channel.name: channel}

    def get(self, channel_name: str) -> Optional[Channel]:
        if (channel := self.name_cache.get(channel_name)): return channel

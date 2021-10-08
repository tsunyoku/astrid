from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from constants.privileges import Privileges, ClientPrivileges
from constants.modes import osuModes
from objects.channel import Channel
from constants.mods import Mods
from utils.logging import info
from objects.clan import Clan
from packets import writer
from objects import glob

@dataclass
class Stats:
    rscore: int
    acc: float
    pc: int
    tscore: int
    rank: int
    country_rank: int
    pp: int
    max_combo: int
    playtime: int
    grades: dict

class Player:
    def __init__(self, **kwargs) -> None:
        self.id: int = kwargs.get('id')
        self.name: str = kwargs.get('name')

        self.token: str = ''
        self.password_md5: str = ''
        self.utc_offset: int = 0
        self.login_time: int = 0

        self.priv: Privileges = kwargs.get('priv', Privileges(0))
        self.country_iso: str = kwargs.get('country_iso')

        self.country: int = kwargs.get('country')
        self.loc: list = kwargs.get('loc', [0.0, 0.0])

        self.friends: list = []
        
        self.queue = bytearray()

        self.action: int = 0
        self.action_info: str = ''
        self.map_md5: str = ''
        self.mods: Mods = Mods(0)
        self.mode: osuModes = osuModes(0)
        self.map_id: int = 0

        self.stats: dict = {}
        self.achievements: list = []
        self.spectators: list = []
        self.spectating: Optional['Player'] = None
        self.channels: list = []
        #self.match: Optional['Match'] = None
        #self.last_np: Optional['Beatmap'] = None
        #self.last_score: Optional['Score'] = None
        self.clan: Optional['Clan'] = None

        self.last_ping: int = 0
        self.freeze_timer: int = kwargs.get('freeze_timer', 0)
        self.registered_at: int = kwargs.get('registered_at', 0)
        self.silence_end: int = kwargs.get('silence_end', 0)
        self.donor_end: int = kwargs.get('donor_end', 0)

        self.encrypted_password: str = kwargs.get('encrypted_password')
        self.tourney_client: bool = kwargs.get('tourney_client')
        
        self.pp_lb: bool = kwargs.get('pp_lb', False)
        self.lobby: bool = False
        self.online: bool = False

    @property
    def mode_vn(self) -> int: return self.mode.as_vn

    @property
    def full_name(self) -> str:
        if self.clan: return f'[{self.clan.tag}] {self.name}'
        else: return self.name

    @property
    def safe_name(self) -> str: return self.name.lower().replace(' ', '_')

    @property
    def current_stats(self) -> Stats: return self.stats[self.mode.value]

    @property
    def restricted(self) -> bool: return self.priv & Privileges.Restricted

    @property
    def banned(self) -> bool: return self.priv & Privileges.Banned

    @property
    def disallowed(self) -> bool: return self.priv & Privileges.Disallowed

    @property
    def frozen(self) -> bool: return self.priv & Privileges.Frozen

    def enqueue(self, data: bytes) -> None: self.queue += data

    @property
    def client_priv(self) -> ClientPrivileges:
        priv = ClientPrivileges(0)
        priv |= ClientPrivileges.Player

        if self.disallowed: return priv

        if self.priv & Privileges.Admin:
            priv |= ClientPrivileges.Moderator
        if self.priv & Privileges.Developer:
            priv |= ClientPrivileges.Developer
        if self.priv & Privileges.Owner:
            priv |= ClientPrivileges.Owner

        return priv

    @classmethod
    async def login(cls, user: dict) -> 'Player':
        self = cls(
            id=user['id'],
            name=user['name'],
            token=user.get('token'),
            utc_offset=user.get('utc_offset'),
            login_time=user.get('ltime'),
            country_iso=user.get('country_iso'),
            country=user['country'],
            loc=[user.get('lon', 0.0), user.get('lat', 0.0)],
            password_md5=user.get('password_md5'),
            priv=Privileges(user['priv']),
            freeze_timer=datetime.fromtimestamp(user['freeze_timer']),
            encrypted_password=user.get('pw'),
            donor_end=user.get('donor_end'),
            silence_end=user.get('silence_end')
        )

        if self.password_md5: self.password = self.password.decode()

        self.friends = []
        async for u in glob.sql.iter('SELECT user2 FROM friends WHERE user1 = %s', [self.id]): self.friends.append(u['user2'])

        if (clan := user.get('clan')): self.clan = glob.clans.get(id=clan)

        async for achievement in glob.sql.iter(f'SELECT ach FROM user_achievements WHERE uid = %s', [self.id]):
            ...
            #for _achievement in glob.achievements:
                #if achievement['ach'] == _achievement.id: self.achievements += achievement

        return self

    def logout(self) -> None:
        self.token = ''
        self.online = False

        if not self.disallowed: glob.players.enqueue(writer.logout(self.id))
        for channel in self.channels: self.leave_channel(channel)

        info(f"{self.name} logged out.")

    async def set_stats(self) -> None:
        for mode in osuModes:
            stat = await glob.sql.fetchrow(
                'SELECT rscore_{0} rscore, acc_{0} acc, pc_{0} pc, '
                'tscore_{0} tscore, pp_{0} pp, mc_{0} max_combo, '
                'pt_{0} playtime FROM stats WHERE id = %s'.format(mode.name),
                [self.id]
            )

            if not stat: continue

            grades = await glob.sql.fetchrow(
                'SELECT xh_{0} xh, x_{0} x, sh_{0} sh, s_{0} s, a_{0} a FROM stats WHERE id = %s'.format(mode.name),
                [self.id]
            )

            stat['grades'] = {}
            for grade in ('xh', 'x', 'sh', 's', 'a'): stat['grades'][grade] = grades[grade]

            stat['rank'] = await self.get_rank(mode, stat['pp'])
            stat['country_rank'] = await self.get_rank(mode, stat['pp'])

            self.stats[mode.value] = Stats(**stat)

    async def get_rank(self, mode: osuModes, pp: int) -> int:
        if self.disallowed: return 0

        redis_rank = await glob.redis.zrevrank(f'astrid:leaderboard:{mode.name}', self.id)
        if redis_rank is None: return 1 if pp > 0 else 0
        else: return redis_rank + 1

    async def get_country_rank(self, mode: osuModes, pp: int) -> int:
        if self.disallowed: return 0

        redis_rank = await glob.redis.zrevrank(f'astrid:leaderboard:{mode.name}:{self.country_iso}', self.id)
        if redis_rank is None: return 1 if pp > 0 else 0
        else: return redis_rank + 1

    def dequeue(self) -> Optional[bytes]:
        if self.queue:
            packet_data = bytes(self.queue)

            self.queue.clear()
            return packet_data

    def receive_message(self, message: str, sent_by: 'Player') -> None: # unsure of this naming convention?
        self.enqueue(
            writer.sendMessage(
                sent_by.name,
                message,
                self.name,
                sent_by.id
            )
        )

    def join_channel(self, channel: Channel) -> None:
        if (
            self in channel.players or
            (channel.name == '#lobby' and not self.lobby)
        ):
            return

        channel.add(self)
        self.channels.append(channel)

        self.enqueue(
            writer.channelJoin(channel.name)
        )

        channel.enqueue(
            writer.channelInfo(channel)
        )

        info(f"{self.name} joined {channel.name}")

    def leave_channel(self, channel: Channel) -> None:
        if self not in channel.players: return

        channel.remove(self)
        self.channels.remove(channel)

        self.enqueue(
            writer.channelKick(channel.name)
        )

        channel.enqueue(
            writer.channelInfo(channel)
        )

        info(f"{self.name} left {channel.name}")

    def add_spectator(self, user: 'Player') -> None:
        if not (spec_channel := glob.channels.get(f"#spec_{self.id}")):
            spec_channel = Channel(
                name="#spectator",
                desc=f"Spectator channel for {self.name}",
                auto_join=False,
                permanent_channel=False
            )

            self.join_channel(spec_channel)
            glob.channels.add_channel(spec_channel)

        user.join_channel(spec_channel)

        join_packet = writer.spectatorJoined(user.id)
        for p in self.spectators:
            p.enqueue(join_packet)
            user.enqueue(writer.spectatorJoined(p.id))

        self.spectators.append(user)
        user.spectating = self

        self.enqueue(writer.hostSpectatorJoined(user.id))
        info(f"{user.name} started spectating {self.name}")

    def remove_spectator(self, user: 'Player') -> None:
        self.spectators.remove(user)
        user.spectating = None

        if not (spec_channel := glob.channels.get(f"#spec_{self.id}")): return
        user.leave_channel(spec_channel)

        if not self.spectators: self.leave_channel(spec_channel)
        else:
            channel_packet = writer.channelInfo(spec_channel)
            for u in self.spectators:
                u.enqueue(writer.spectatorLeft(user.id))
                u.enqueue(channel_packet)

            self.enqueue(channel_packet)

        self.enqueue(writer.hostSpectatorLeft(user.id))
        info(f"{user.name} stopped spectating {self.name}")
        

        


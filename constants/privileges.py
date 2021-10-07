from typing import Optional
from enum import IntFlag

from utils.general import pymysql_encode, escape_enum

@pymysql_encode(escape_enum)
class Privileges(IntFlag):
    Normal = 1 << 0
    Verified = 1 << 1
    Supporter = 1 << 2

    Nominator = 1 << 3
    Admin = 1 << 4
    Developer = 1 << 5
    Owner = 1 << 6

    Restricted = 1 << 7
    Banned = 1 << 8

    BypassAnticheat = 1 << 9
    Frozen = 1 << 10
    Whitelisted = 1 << 11

    Tourney = 1 << 12

    Staff = Nominator | Admin | Developer | Owner
    Manager = Admin | Developer | Owner | Tourney
    Master = Normal | Verified | Supporter | Nominator | Admin | Developer | Owner | BypassAnticheat | Whitelisted | Tourney
    Disallowed = Restricted | Banned

    @classmethod
    def get(cls, name) -> Optional['Privileges']:
        if name in cls.__members__:
            return cls[name]

@pymysql_encode(escape_enum)
class ClientPrivileges(IntFlag):
    Player = 1 << 0
    Moderator = 1 << 1
    Supporter = 1 << 2
    Owner = 1 << 3
    Developer = 1 << 4
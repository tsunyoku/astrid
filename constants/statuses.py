from enum import IntEnum

from utils.general import pymysql_encode, escape_enum

@pymysql_encode(escape_enum)
class mapStatus(IntEnum):
    NotSubmitted = -1
    Pending = 0
    Update = 1
    Ranked = 2
    Approved = 3
    Qualified = 4
    Loved = 5

    GIVE_PP = Ranked | Approved

    @classmethod
    def from_api(cls, status: int) -> 'mapStatus':
        if status <= 0: return cls.Pending
        
        return cls(status + 1)

@pymysql_encode(escape_enum)
class scoreStatus(IntEnum):
    Failed = 0
    Submitted = 1
    Best = 2
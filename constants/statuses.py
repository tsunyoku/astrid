from enum import IntEnum


class mapStatuses(IntEnum):
    NotSubmitted = -1
    Pending = 0
    Update = 1
    Ranked = 2
    Approved = 3
    Qualified = 4
    Loved = 5

    GIVE_PP = Ranked | Approved

    @classmethod
    def from_api(cls, status: int) -> 'mapStatuses':
        if status in (-2, -1, 0): return cls.Pending
        if status in (1, 2, 3, 4): return cls(status + 1)

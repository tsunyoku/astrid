from typing import Callable

class Achievement:
    def __init__(self, **kwargs) -> None:
        self.id: int = kwargs.get("id")
        self.image: str = kwargs.get("image")
        self.name: str = kwargs.get("name")
        self.desc: str = kwargs.get("desc")
        self.cond: Callable = kwargs.get("cond")
        self.custom: bool = kwargs.get("custom")

    def __repr__(self) -> str: return f"{self.image}+{self.name}+{self.desc}"
from typing import Any, Optional
from dataclasses import dataclass

from utils.general import now

@dataclass
class CacheObject:
    """Serves as an object for each cache identifier."""

    identifier: Any
    expires_at: int
    value: Any

class Cache:
    """A base class that aims to cache pretty much anything via lru caching."""

    def __init__(self, length: int = 300, limit: int = 500):
        """
        Initialises a cache object

        Arguments:
            length (int): How long in seconds before a cache objects is removed.
            limit (int): How many objects can be cached before old objects start to be removed.
        """

        self._cache: list = [] # list of cache objects
        self._length: int = length
        self._limit: int = limit

    def __len__(self) -> int: return len(self._cache)

    def add(self, cache_identifier: Any, cache_value: Any) -> None:
        """
        Adds or updates a value to the cache.

        Arguments:
            cache_identifier (Any): Main identifier for a new cache value; usually a string, int, dict or tuple.
            cache_value (Any): The value to store in cache.
        """

        new_obj = CacheObject(
            identifier=cache_identifier,
            expires_at=now() + self._length,
            value=cache_value
        )

        if not (obj := self.get(cache_identifier, get_object=True)): self._cache.append(new_obj)
        else: # i dont know if setting like this is actually necessary but i think cus its a local i have to
            obj.expires_at = new_obj.expires_at
            obj.value = new_obj.value

        self.overlook_cache()

    def get(self, cache_identifier: Any, get_object: bool = False) -> Optional[Any]:
        """
        Gets the value of a cache object by its given identifier, if it exists.

        Arguments:
            cache_identifier (Any): the identifier to search for.
            get_object (Bool): whether it should return the value or the raw CacheObject
        """

        for _obj in self._cache:
            if _obj.identifier == cache_identifier: return _obj.value if not get_object else _obj

    def remove(self, cache_object: CacheObject) -> None:
        """Removes a cache object from cache."""

        try: self._cache.remove(cache_object)
        except (KeyError, ValueError): pass

    def _overlook_expired(self) -> None:
        """Checks for any cache values that have expired, and removes where necessary."""

        for _obj in self._cache: 
            if _obj.expires_at < now(): self.remove(_obj)

    def _overlook_limited(self) -> None:
        """Checks for cache limit overflow, and removes where necessary."""

        overboard_count = len(self._cache) - self._limit
        if overboard_count > 0: del self._cache[:overboard_count]

    def overlook_cache(self) -> None:
        """Overlooks the current cache to remove any objects where necessary."""

        self._overlook_expired()
        self._overlook_limited()

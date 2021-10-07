from utils.password import verify_password

class PasswordCache:
    def __init__(self) -> None:
        self._cache: dict = {}

    def cache_password(self, password_md5: str, encrypted_password: str) -> None: self._cache |= {password_md5: encrypted_password}

    def verify_password(self, password_md5: str, encrypted_password: str) -> bool:
        if (cached_result := self._cache.get(password_md5)): return cached_result == encrypted_password
        return verify_password(password_md5, encrypted_password)
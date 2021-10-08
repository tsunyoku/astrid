from cryptography.hazmat.backends import default_backend as backend
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand
from cryptography.hazmat.primitives import hashes

from objects import glob

import hashlib

def hash_md5(password: str) -> str: return hashlib.md5(password.encode()).hexdigest().decode()
def encrypt_password(password: str) -> bytes: return password.encode('ISO-8859-1').decode('unicode-escape').encode('ISO-8859-1')

def verify_password(password_md5: bytes, encrypted_password: bytes) -> bool:
    try:
        k = HKDFExpand(
            algorithm=hashes.SHA256(), 
            length=32, 
            info=b'', 
            backend=backend()
        )

        k.verify(password_md5, encrypted_password)
        glob.password_cache.cache_password(password_md5, encrypted_password)

        return True
    except Exception: return False

def generate_password(password_md5: str) -> str:
    k = HKDFExpand(
        algorithm=hashes.SHA256(), 
        length=32, 
        info=b'', 
        backend=backend()
    )

    encrypted_password = k.derive(password_md5).decode('unicode-escape')
    glob.password_cache.cache_password(password_md5, encrypt_password(encrypted_password))

    return encrypted_password
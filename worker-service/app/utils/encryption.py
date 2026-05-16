import os
from cryptography.fernet import Fernet

_ENCRYPTION_KEY = os.getenv("FILE_ENCRYPTION_KEY", "")

def _get_fernet() -> Fernet:
    if not _ENCRYPTION_KEY:
        raise ValueError("FILE_ENCRYPTION_KEY is not set in environment variables.")
    return Fernet(_ENCRYPTION_KEY.encode() if isinstance(_ENCRYPTION_KEY, str) else _ENCRYPTION_KEY)

def decrypt_file_data(ciphertext: bytes) -> bytes:
    f = _get_fernet()
    return f.decrypt(ciphertext)

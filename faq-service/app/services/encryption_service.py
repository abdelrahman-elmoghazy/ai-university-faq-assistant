"""
Encryption Service — Team Member 5
Fernet symmetric encryption for file-at-rest protection.
Key is loaded from the FILE_ENCRYPTION_KEY environment variable.

Generate a key:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import os
import hashlib
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# ── Load key from environment ────────────────────────────────
_ENCRYPTION_KEY = os.getenv("FILE_ENCRYPTION_KEY", "")


def _get_fernet() -> Fernet:
    """Return a Fernet instance. Raises if key is missing or invalid."""
    if not _ENCRYPTION_KEY:
        raise ValueError("FILE_ENCRYPTION_KEY is not set in environment variables.")
    return Fernet(_ENCRYPTION_KEY.encode() if isinstance(_ENCRYPTION_KEY, str) else _ENCRYPTION_KEY)


# ── Public API ───────────────────────────────────────────────

def calculate_sha256(data: bytes) -> str:
    """Calculate SHA-256 hash of raw bytes and return hex digest."""
    return hashlib.sha256(data).hexdigest()


def encrypt_file_data(plaintext: bytes) -> bytes:
    """Encrypt raw file bytes using Fernet. Returns ciphertext bytes."""
    f = _get_fernet()
    return f.encrypt(plaintext)


def decrypt_file_data(ciphertext: bytes) -> bytes:
    """Decrypt Fernet-encrypted bytes. Returns original plaintext bytes."""
    f = _get_fernet()
    return f.decrypt(ciphertext)


def verify_integrity(stored_hash: str, ciphertext: bytes) -> dict:
    """
    Decrypt file in memory, recompute SHA-256, compare with stored hash.
    Returns a dict with integrity_status and details.
    """
    try:
        plaintext = decrypt_file_data(ciphertext)
        current_hash = calculate_sha256(plaintext)

        if current_hash == stored_hash:
            return {
                "integrity_status": "valid",
                "stored_hash": stored_hash,
                "computed_hash": current_hash,
                "message": "File integrity verified — no modifications detected."
            }
        else:
            return {
                "integrity_status": "modified_or_corrupted",
                "stored_hash": stored_hash,
                "computed_hash": current_hash,
                "message": "File integrity check FAILED — file has been modified or corrupted."
            }
    except Exception as e:
        logger.error(f"Integrity verification failed: {e}")
        return {
            "integrity_status": "error",
            "message": "Could not verify file integrity. Decryption failed."
        }

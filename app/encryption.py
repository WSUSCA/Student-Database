import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


class EncryptionError(RuntimeError):
    """Custom error for encryption/decryption failures."""


def _get_fernet_key() -> str:
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise EncryptionError("ENCRYPTION_KEY environment variable is required for encryption.")
    return key


def _build_fernet() -> Fernet:
    try:
        return Fernet(_get_fernet_key())
    except (ValueError, TypeError) as exc:
        raise EncryptionError("Invalid ENCRYPTION_KEY provided.") from exc


def encrypt_text(plain_text: Optional[str]) -> Optional[str]:
    if plain_text is None:
        return None
    fernet = _build_fernet()
    return fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_text(cipher_text: Optional[str]) -> Optional[str]:
    if cipher_text is None:
        return None
    fernet = _build_fernet()
    try:
        return fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise EncryptionError("Unable to decrypt text; token invalid or key mismatch.") from exc

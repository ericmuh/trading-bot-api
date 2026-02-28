from __future__ import annotations

from cryptography.fernet import Fernet

from app.config import get_settings


def _build_cipher() -> Fernet:
    settings = get_settings()
    key = settings.app_encryption_key
    if not key:
        key = Fernet.generate_key().decode("utf-8")
    return Fernet(key.encode("utf-8"))


class CryptoService:
    def __init__(self) -> None:
        self._cipher = _build_cipher()

    def encrypt(self, value: str) -> str:
        return self._cipher.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        return self._cipher.decrypt(value.encode("utf-8")).decode("utf-8")

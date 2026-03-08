import base64
import os

import pytest

from app.core.security import decrypt_credential, encrypt_credential


@pytest.mark.asyncio
async def test_encrypt_decrypt_roundtrip(monkeypatch):
    key = base64.b64encode(os.urandom(32)).decode("utf-8")
    monkeypatch.setenv("MT5_ENCRYPTION_KEY", key)

    plaintext = "my-secret-password"
    encrypted = encrypt_credential(plaintext)

    assert isinstance(encrypted, bytes)
    assert encrypted != plaintext.encode("utf-8")
    assert decrypt_credential(encrypted) == plaintext


def test_ciphertext_not_plaintext(monkeypatch):
    key = base64.b64encode(os.urandom(32)).decode("utf-8")
    monkeypatch.setenv("MT5_ENCRYPTION_KEY", key)

    encrypted = encrypt_credential("plaintext")
    assert b"plaintext" not in encrypted

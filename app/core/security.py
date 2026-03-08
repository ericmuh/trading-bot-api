import uuid
import os
import base64
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _algorithm() -> str:
    return settings.JWT_ALGORITHM


def _encode(payload: dict) -> str:
    key = settings.JWT_PRIVATE_KEY if _algorithm().startswith("RS") else settings.SECRET_KEY
    return jwt.encode(payload, key, algorithm=_algorithm())


def _decode(token: str) -> dict:
    key = settings.JWT_PUBLIC_KEY if _algorithm().startswith("RS") else settings.SECRET_KEY
    return jwt.decode(token, key, algorithms=[_algorithm()])


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
    }
    return _encode(payload)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": jti,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
    }
    return _encode(payload), jti


def decode_token(token: str) -> dict:
    try:
        return _decode(token)
    except JWTError as error:
        raise ValueError(f"Invalid token: {error}") from error


def get_encryption_key() -> bytes:
    key_b64 = os.environ.get("MT5_ENCRYPTION_KEY")
    if not key_b64:
        raise RuntimeError("MT5_ENCRYPTION_KEY not set")
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise RuntimeError("MT5_ENCRYPTION_KEY must decode to 32 bytes")
    return key


def encrypt_credential(plaintext: str) -> bytes:
    key = get_encryption_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_credential(data: bytes) -> str:
    key = get_encryption_key()
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")

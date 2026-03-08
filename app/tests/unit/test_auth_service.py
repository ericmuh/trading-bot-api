from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_hash_and_verify_password():
    hashed = hash_password("Password123!")
    assert verify_password("Password123!", hashed)


def test_access_token_contains_subject():
    token = create_access_token("user-1")
    decoded = decode_token(token)
    assert decoded["sub"] == "user-1"
    assert decoded["type"] == "access"

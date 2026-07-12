from app.core.security import (
    create_access_token,
    decode_access_token,
    decrypt_secret,
    encrypt_secret,
    hash_password,
    verify_password,
)


def test_password_round_trip():
    encoded = hash_password("strong-password")
    assert verify_password("strong-password", encoded)
    assert not verify_password("wrong-password", encoded)


def test_token_round_trip():
    token = create_access_token(42)
    assert decode_access_token(token) == 42


def test_encryption_round_trip():
    encrypted = encrypt_secret("broker-secret")
    assert encrypted != "broker-secret"
    assert decrypt_secret(encrypted) == "broker-secret"


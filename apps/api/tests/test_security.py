import pytest
from fastapi import HTTPException


def test_hash_password_returns_bcrypt_hash():
    from core.security import hash_password
    hashed = hash_password("mysecretpassword")
    assert hashed.startswith("$2b$")
    assert hashed != "mysecretpassword"


def test_verify_password_correct():
    from core.security import hash_password, verify_password
    hashed = hash_password("mysecretpassword")
    assert verify_password("mysecretpassword", hashed) is True


def test_verify_password_wrong():
    from core.security import hash_password, verify_password
    hashed = hash_password("mysecretpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token_decodes():
    from core.security import create_access_token, decode_token
    token = create_access_token("user-id-123", "org-id-456")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-123"
    assert payload["org_id"] == "org-id-456"
    assert payload["type"] == "access"


def test_create_refresh_token_decodes():
    from core.security import create_refresh_token, decode_token
    token = create_refresh_token("user-id-123", "org-id-456")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-123"
    assert payload["org_id"] == "org-id-456"
    assert payload["type"] == "refresh"


def test_decode_token_invalid_raises_401():
    from core.security import decode_token
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.valid.token")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "TOKEN_INVALID"

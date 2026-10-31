import pytest

from server.app.security.password import hash_password, verify_password


def test_hashes_use_unique_salts_and_verify():
    first = hash_password("TestOnly123")
    second = hash_password("TestOnly123")
    assert first != second
    assert first.startswith("scrypt:")
    assert verify_password("TestOnly123", first)
    assert not verify_password("Wrong123", first)


@pytest.mark.parametrize("invalid", ["", None, 123])
def test_empty_or_invalid_password_cannot_be_hashed(invalid):
    with pytest.raises(ValueError):
        hash_password(invalid)


@pytest.mark.parametrize(
    "password,stored_hash", [(None, "hash"), ("test", None), ("test", "bad")]
)
def test_invalid_hash_input_fails_safely(password, stored_hash):
    assert verify_password(password, stored_hash) is False

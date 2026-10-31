import pytest
from sqlalchemy.exc import IntegrityError

from server.app.extensions import db
from server.app.models import User
from server.app.security.password import hash_password


def account(**overrides):
    values = {
        "full_name": "Test Resident",
        "email": "resident@example.test",
        "password_hash": hash_password("TestOnly123"),
    }
    return User(**(values | overrides))


def test_user_has_safe_defaults(app):
    user = account(email="  RESIDENT@EXAMPLE.TEST ")
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    assert user.email == "resident@example.test"
    assert user.role == "Resident"
    assert user.is_active is True
    assert user.failed_login_count == 0
    assert user.created_at is not None
    assert user.password_hash.startswith("scrypt:")
    assert not hasattr(user, "password")


def test_duplicate_email_is_rejected(app):
    db.session.add(account())
    db.session.commit()
    db.session.add(account(email="RESIDENT@EXAMPLE.TEST"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
    assert db.session.query(User).count() == 1


@pytest.mark.parametrize(
    "overrides",
    [{"role": "SuperAdmin"}, {"full_name": "  "}, {"failed_login_count": -1}],
)
def test_database_rejects_invalid_account_values(app, overrides):
    db.session.add(account(**overrides))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_account_requires_password_hash(app):
    db.session.add(User(full_name="Test", email="test@example.test"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()

from datetime import timedelta

import pytest

from server.app.extensions import db
from server.app.models import AuthSession, User
from server.app.security.access import utc_now
from server.app.security.password import hash_password, verify_password


def post(client, path, body=None):
    token = client.get("/api/auth/csrf").json["csrf_token"]
    return client.post(path, json=body, headers={"X-CSRFToken": token})


def register(client, **overrides):
    values = dict(
        name="Test Resident",
        email="resident@example.test",
        password="TestOnly123",
        confirm_password="TestOnly123",
    )
    return post(client, "/api/auth/register", values | overrides)


def login(client, **overrides):
    return post(
        client,
        "/api/auth/login",
        dict(email="resident@example.test", password="TestOnly123") | overrides,
    )


def test_signup_persists_and_logs_in_with_resident_role(client, app):
    response = register(client, email="  RESIDENT@EXAMPLE.TEST ", role="Administrator")
    assert response.status_code == 201
    assert response.json["user"]["role"] == "Resident"
    assert set(response.json["user"]) == {"id", "name", "email", "role"}
    user = db.session.scalar(db.select(User))
    assert user.email == "resident@example.test"
    assert verify_password("TestOnly123", user.password_hash)
    assert client.get("/api/auth/me").json["user"]["id"] == user.id
    assert client.get("/api/resident/dashboard").status_code == 200
    assert db.session.query(AuthSession).count() == 1


@pytest.mark.parametrize(
    "overrides,field",
    [
        ({"name": ""}, "name"),
        ({"name": "x" * 101}, "name"),
        ({"email": "bad"}, "email"),
        ({"email": "a" * 250 + "@a.test"}, "email"),
        ({"password": "short1"}, "password"),
        ({"password": "lettersOnly"}, "password"),
        ({"password": "12345678"}, "password"),
        ({"password": "a1" * 65}, "password"),
        ({"confirm_password": "Different1"}, "confirm_password"),
        ({"email": 123}, "email"),
    ],
)
def test_signup_rejects_invalid_fields_without_saving(client, overrides, field):
    response = register(client, **overrides)
    assert response.status_code == 400
    assert field in response.json["errors"]
    assert db.session.query(User).count() == 0


def test_duplicate_email_is_case_insensitive(client):
    assert register(client).status_code == 201
    assert register(client, email="RESIDENT@EXAMPLE.TEST").status_code == 409
    assert db.session.query(User).count() == 1


def test_csrf_required_for_all_auth_mutations(client):
    for path in ["register", "login", "logout"]:
        response = client.post(f"/api/auth/{path}", json={})
        assert response.status_code == 400
        assert response.json["code"] == "CSRF_FAILED"
    assert db.session.query(User).count() == 0


def test_login_cookie_is_http_only_samesite_and_rotates(client):
    register(client)
    before = client.get_cookie("fixit_session").value
    response = login(client)
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["Set-Cookie"]
    assert "SameSite=Lax" in response.headers["Set-Cookie"]
    assert client.get_cookie("fixit_session").value != before
    assert db.session.query(AuthSession).count() == 1
    assert client.get("/api/auth/me").status_code == 200


def test_cookie_secure_flag_in_production_config(client, app):
    app.config["SESSION_COOKIE_SECURE"] = True
    response = client.get("/api/auth/csrf")
    assert "Secure" in response.headers["Set-Cookie"]


def test_logout_revokes_old_cookie_and_is_idempotent(client, app):
    register(client)
    stolen_cookie = client.get_cookie("fixit_session").value
    assert post(client, "/api/auth/logout").status_code == 204
    assert db.session.query(AuthSession).count() == 0
    assert client.get("/api/auth/me").status_code == 401
    attacker = app.test_client()
    attacker.set_cookie("fixit_session", stolen_cookie)
    assert attacker.get("/api/auth/me").status_code == 401
    assert post(client, "/api/auth/logout").status_code == 204


def test_unknown_email_and_wrong_password_have_same_error(client):
    register(client)
    wrong = login(client, password="Wrong123")
    unknown = login(client, email="missing@example.test", password="Wrong123")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json == unknown.json


def test_five_failures_lock_even_correct_password_and_expiry_resets(client):
    register(client)
    post(client, "/api/auth/logout")
    for attempt in range(5):
        assert login(client, password="Wrong123").status_code == (
            429 if attempt == 4 else 401
        )
    assert login(client).status_code == 429
    user = db.session.scalar(db.select(User))
    user.locked_until = utc_now() - timedelta(seconds=1)
    db.session.commit()
    assert login(client).status_code == 200
    db.session.refresh(user)
    assert user.failed_login_count == 0
    assert user.locked_until is None


def test_successful_login_resets_failures(client):
    register(client)
    for _ in range(4):
        assert login(client, password="Wrong123").status_code == 401
    assert login(client).status_code == 200
    assert login(client, password="Wrong123").status_code == 401
    assert db.session.scalar(db.select(User)).failed_login_count == 1


def test_expired_session_cannot_be_used(client):
    register(client)
    record = db.session.scalar(db.select(AuthSession))
    record.expires_at = utc_now() - timedelta(seconds=1)
    db.session.commit()
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json["code"] == "SESSION_EXPIRED"
    assert db.session.query(AuthSession).count() == 0


def test_active_session_expiry_rolls_forward(client):
    register(client)
    record = db.session.scalar(db.select(AuthSession))
    record.expires_at = utc_now() + timedelta(minutes=1)
    db.session.commit()
    client.get("/api/auth/me")
    db.session.refresh(record)
    assert record.expires_at.replace(tzinfo=utc_now().tzinfo) > utc_now() + timedelta(
        minutes=55
    )


def test_deactivation_blocks_current_session_and_login(client):
    register(client)
    user = db.session.scalar(db.select(User))
    user.is_active = False
    db.session.commit()
    assert client.get("/api/auth/me").status_code == 401
    assert login(client).status_code == 403
    assert (
        login(client, password="Wrong123").json["message"]
        == "Incorrect email or password"
    )


def test_role_is_checked_in_database_not_only_browser(client, app):
    assert client.get("/api/admin/dashboard").status_code == 401
    register(client)
    assert client.get("/api/admin/dashboard").status_code == 403
    admin = User(
        full_name="Test Admin",
        email="admin@example.test",
        password_hash=hash_password("TestAdmin123"),
        role="Administrator",
    )
    db.session.add(admin)
    db.session.commit()
    separate = app.test_client()
    assert (
        login(separate, email="admin@example.test", password="TestAdmin123").status_code
        == 200
    )
    assert separate.get("/api/admin/dashboard").status_code == 200
    assert separate.get("/api/resident/dashboard").status_code == 403


def test_user_role_is_rechecked_for_existing_session(client):
    register(client)
    user = db.session.scalar(db.select(User))
    user.role = "Administrator"
    db.session.commit()
    assert client.get("/api/resident/dashboard").status_code == 403
    assert client.get("/api/admin/dashboard").status_code == 200


def test_tampered_cookie_and_private_cache_headers(client):
    register(client)
    client.set_cookie("fixit_session", "not-a-signed-cookie")
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.headers["Cache-Control"] == "no-store"


def test_administrator_cli_hashes_password_and_rejects_duplicates(app):
    args = [
        "create-admin",
        "--name",
        "Test Admin",
        "--email",
        "ADMIN@EXAMPLE.TEST",
        "--password",
        "TestAdmin123",
    ]
    result = app.test_cli_runner().invoke(args=args)
    assert result.exit_code == 0
    user = db.session.scalar(db.select(User))
    assert user.role == "Administrator"
    assert verify_password("TestAdmin123", user.password_hash)
    assert app.test_cli_runner().invoke(args=args).exit_code != 0


def test_bad_json_body_is_rejected(client):
    response = post(client, "/api/auth/register", ["not", "an", "object"])
    assert response.status_code == 400
    assert db.session.query(User).count() == 0


def test_bad_csrf_token_cannot_revoke_login(client):
    register(client)
    response = client.post("/api/auth/logout", headers={"X-CSRFToken": "fake"})
    assert response.status_code == 400
    assert client.get("/api/auth/me").status_code == 200

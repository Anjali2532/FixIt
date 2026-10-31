from datetime import datetime, timezone
from functools import wraps
import hashlib
import secrets

from flask import current_app, g, jsonify, session

from ..extensions import db
from ..models import AuthSession, User


def utc_now():
    return datetime.now(timezone.utc)


def aware(value):
    # SQLite returns naive datetimes; PostgreSQL preserves the timezone.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def public_user(user):
    return {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
        "role": user.role,
    }


def remove_login():
    token = session.get("auth_id")
    if isinstance(token, str):
        record = db.session.get(AuthSession, token_digest(token))
        if record:
            db.session.delete(record)
    session.clear()
    g.user = None


def start_login(user):
    """Rotate the identifier and commit account changes and login together."""
    remove_login()
    token = secrets.token_urlsafe(32)
    db.session.add(
        AuthSession(
            token_hash=token_digest(token),
            user_id=user.id,
            expires_at=utc_now() + current_app.permanent_session_lifetime,
        )
    )
    db.session.commit()
    session["auth_id"] = token
    session.permanent = True
    g.user = user
    g.pop("csrf_token", None)


def load_user():
    g.user = None
    g.session_expired = False
    token = session.get("auth_id")
    if not isinstance(token, str):
        return
    record = db.session.get(AuthSession, token_digest(token))
    user = db.session.get(User, record.user_id) if record else None
    if (
        not record
        or aware(record.expires_at) <= utc_now()
        or not user
        or not user.is_active
    ):
        remove_login()
        db.session.commit()
        g.session_expired = True
        return
    record.expires_at = utc_now() + current_app.permanent_session_lifetime
    db.session.commit()
    g.user = user


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            expired = g.get("session_expired", False)
            return (
                jsonify(
                    message=(
                        "Your session has expired. Please log in again."
                        if expired
                        else "Please log in to continue."
                    ),
                    code="SESSION_EXPIRED" if expired else "UNAUTHENTICATED",
                ),
                401,
            )
        return view(*args, **kwargs)

    return wrapped


def require_role(role):
    def decorate(view):
        @wraps(view)
        @require_auth
        def wrapped(*args, **kwargs):
            if g.user.role != role:
                current_app.logger.warning(
                    "Access denied: user=%s role=%s", g.user.id, g.user.role
                )
                return (
                    jsonify(
                        message="You do not have permission to access this page.",
                        code="FORBIDDEN",
                    ),
                    403,
                )
            return view(*args, **kwargs)

        return wrapped

    return decorate

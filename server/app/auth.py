from datetime import timedelta
import re
import secrets

from flask import Blueprint, current_app, g, jsonify, request
from flask_wtf.csrf import generate_csrf
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .extensions import db, limiter
from .models import User
from .security.access import (
    aware,
    public_user,
    remove_login,
    require_auth,
    start_login,
    utc_now,
)
from .security.password import hash_password, verify_password

auth = Blueprint("auth", __name__, url_prefix="/api/auth")
_DUMMY_HASH = hash_password(secrets.token_urlsafe(32))
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def request_values():
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


def value(body, key):
    candidate = body.get(key)
    return candidate if isinstance(candidate, str) else ""


def signup_errors(body):
    name = value(body, "name").strip()
    email = value(body, "email").strip().lower()
    password = value(body, "password")
    errors = {}
    if not name or len(name) > 100:
        errors["name"] = "Enter your name using 1–100 characters."
    if len(email) > 255 or not EMAIL.fullmatch(email):
        errors["email"] = "Please enter a valid email address."
    if (
        not 8 <= len(password) <= 128
        or not re.search(r"[A-Za-z]", password)
        or not re.search(r"[0-9]", password)
    ):
        errors["password"] = (
            "Use 8–128 characters with at least one letter and one number."
        )
    if password != value(body, "confirm_password"):
        errors["confirm_password"] = "Passwords do not match."
    return errors


@auth.get("/csrf")
def csrf_token():
    # Always issue against this browser's current session, including after logout.
    g.pop("csrf_token", None)
    return jsonify(csrf_token=generate_csrf())


@auth.post("/register")
@limiter.limit("10 per minute")
def register():
    body = request_values()
    errors = signup_errors(body)
    if errors:
        return (
            jsonify(message="Please check the highlighted fields.", errors=errors),
            400,
        )
    user = User(
        full_name=value(body, "name").strip(),
        email=value(body, "email"),
        password_hash=hash_password(value(body, "password")),
        role="Resident",  # Public registration never accepts a supplied role.
    )
    try:
        db.session.add(user)
        db.session.flush()
        start_login(user)
    except IntegrityError:
        db.session.rollback()
        return (
            jsonify(
                message="An account with this email already exists. Please log in instead.",
                errors={"email": "This email is already registered."},
            ),
            409,
        )
    return jsonify(user=public_user(user), csrf_token=generate_csrf()), 201


@auth.post("/login")
@limiter.limit("20 per minute")
def login():
    body = request_values()
    email = value(body, "email").strip().lower()
    password = value(body, "password")
    if not email or not password or len(email) > 255 or len(password) > 128:
        return (
            jsonify(
                message="Email and password are required (password maximum 128 characters)."
            ),
            400,
        )
    user = db.session.scalar(select(User).where(User.email == email).with_for_update())
    now = utc_now()
    if user and user.locked_until and aware(user.locked_until) > now:
        return jsonify(message="Too many failed attempts. Please try again later."), 429
    if user and user.locked_until:
        user.locked_until = None
        user.failed_login_count = 0
    valid = verify_password(password, user.password_hash if user else _DUMMY_HASH)
    if not user or not valid:
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.locked_until = now + timedelta(
                    minutes=current_app.config["LOGIN_LOCK_MINUTES"]
                )
                user.failed_login_count = 0
                db.session.commit()
                return (
                    jsonify(
                        message="Too many failed attempts. Please try again later."
                    ),
                    429,
                )
            db.session.commit()
        return jsonify(message="Incorrect email or password"), 401
    if not user.is_active:
        return (
            jsonify(
                message="This account is not active. Please contact your community manager."
            ),
            403,
        )
    user.failed_login_count = 0
    user.locked_until = None
    start_login(user)
    return jsonify(user=public_user(user), csrf_token=generate_csrf())


@auth.get("/me")
@require_auth
def me():
    return jsonify(user=public_user(g.user))


@auth.post("/logout")
def logout():
    remove_login()
    db.session.commit()
    return "", 204

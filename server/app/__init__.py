"""Create separate Flask applications for development and testing."""

import os
from datetime import timedelta
from pathlib import Path

import click
from flask import Flask, jsonify, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import TooManyRequests
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .extensions import csrf, db, limiter, migrate


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://fixit_app@127.0.0.1:5432/fixit_db",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SESSION_COOKIE_NAME="fixit_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("FIXIT_ENV") == "production",
        SESSION_REFRESH_EACH_REQUEST=True,
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=60),
        LOGIN_LOCK_MINUTES=15,
        MAX_CONTENT_LENGTH=16 * 1024,
        RATELIMIT_STORAGE_URI=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
    )
    if test_config:
        app.config.update(test_config)
    if not app.secret_key:
        if app.testing:
            app.secret_key = "test-only-session-signing-key"
        else:
            raise RuntimeError(
                "Set a long random SECRET_KEY in .env before starting Flask."
            )

    db.init_app(app)
    migrate.init_app(
        app, db, directory=str(Path(__file__).resolve().parent.parent / "migrations")
    )

    from . import models  # Register models before generating migrations.
    from .routes import api
    from .auth import auth
    from .security.access import load_user
    from .security.password import hash_password

    from .issues import issues

    app.register_blueprint(issues)
    app.register_blueprint(api)
    app.register_blueprint(auth)
    csrf.init_app(app)
    limiter.init_app(app)
    app.before_request(load_user)

    @app.after_request
    def private_responses(response):
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return (
            jsonify(
                message="Your security token expired. Please try again.",
                code="CSRF_FAILED",
            ),
            400,
        )

    @app.errorhandler(TooManyRequests)
    def rate_limit_error(error):
        return (
            jsonify(message="Too many requests. Please wait a minute and try again."),
            429,
        )

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.exception("Database request failed")
        return (
            jsonify(
                message="The service is temporarily unavailable. Please try again."
            ),
            503,
        )

    @app.cli.command("create-admin")
    @click.option("--name", prompt="Full name")
    @click.option("--email", prompt="Email")
    @click.password_option()
    def create_admin(name, email, password):
        """Create an administrator locally; public signup creates residents only."""
        from .auth import signup_errors
        from .models import User
        from sqlalchemy.exc import IntegrityError

        errors = signup_errors(
            {
                "name": name,
                "email": email,
                "password": password,
                "confirm_password": password,
            }
        )
        if errors:
            raise click.ClickException(" ".join(errors.values()))
        try:
            db.session.add(
                User(
                    full_name=name.strip(),
                    email=email,
                    password_hash=hash_password(password),
                    role="Administrator",
                )
            )
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise click.ClickException("That email is already registered.") from error
        click.echo("Administrator account created.")

    @app.cli.command("set-account-active")
    @click.option("--email", required=True)
    @click.option("--active/--inactive", default=True)
    def set_account_active(email, active):
        """Activate or deactivate an account without exposing a public admin API."""
        from .models import User

        user = db.session.scalar(
            db.select(User).where(User.email == email.strip().lower())
        )
        if user is None:
            raise click.ClickException("Account not found.")
        user.is_active = active
        db.session.commit()
        click.echo("Account activated." if active else "Account deactivated.")

    @app.cli.command("db-check")
    def db_check():
        """Check connectivity without displaying database credentials."""
        try:
            db.session.execute(text("SELECT 1"))
        except SQLAlchemyError as error:
            db.session.rollback()
            raise click.ClickException(
                "Database unavailable. Check DATABASE_URL and PostgreSQL."
            ) from error
        click.echo("Database connection successful.")

    return app

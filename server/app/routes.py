from flask import Blueprint, current_app, g, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db
from .security.access import public_user, require_role

api = Blueprint("api", __name__, url_prefix="/api")


@api.get("/health")
def health():
    """Confirm Flask is responding independently of the database."""
    return jsonify(status="ok")


@api.get("/ready")
def ready():
    """Report unavailable dependencies without exposing connection details."""
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.warning("Database readiness check failed.")
        return jsonify(status="unavailable", database="unavailable"), 503
    return jsonify(status="ok", database="connected")


@api.get("/resident/dashboard")
@require_role("Resident")
def resident_dashboard():
    return jsonify(
        user=public_user(g.user),
        message="Your account is ready. You can submit and track your reports.",
    )


@api.get("/admin/dashboard")
@require_role("Administrator")
def admin_dashboard():
    return jsonify(
        user=public_user(g.user),
        message="Administrator access is active. You can review reports and update progress.",
    )

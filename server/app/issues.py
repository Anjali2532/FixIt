"""Resident reports and administrator progress updates."""

from flask import Blueprint, current_app, g, jsonify, request, send_file
import uuid
from .photos import save_photo, remove_photo, photo_path
from sqlalchemy import func, or_

from .extensions import db, limiter
from .models import Issue, IssueUpdate
from .security.access import require_auth, require_role, aware

issues = Blueprint("issues", __name__, url_prefix="/api/issues")
CATEGORIES = (
    "Lighting",
    "Roads & Sidewalks",
    "Trash & Recycling",
    "Plumbing",
    "Equipment & Facilities",
    "Safety",
    "Other",
)
STATUSES = ("Reported", "In Progress", "Resolved")
PRIORITIES = ("Low", "Normal", "High")


def serialize(issue):
    return {
        key: getattr(issue, key)
        for key in (
            "id",
            "title",
            "description",
            "location",
            "category",
            "priority",
            "status",
        )
    } | {
        "created_at": aware(issue.created_at).isoformat(),
        "photo_url": f"/api/issues/{issue.id}/photo" if issue.photo_name else None,
    }


def visible_query():
    query = db.select(Issue)
    return (
        query
        if g.user.role == "Administrator"
        else query.where(Issue.user_id == g.user.id)
    )


@issues.get("")
@require_auth
def list_issues():
    query = visible_query()
    counts = {
        status: db.session.scalar(
            db.select(func.count()).select_from(
                query.where(Issue.status == status).subquery()
            )
        )
        for status in STATUSES
    }
    for field, choices in (("status", STATUSES), ("category", CATEGORIES)):
        value = request.args.get(field, "")
        if field == "status" and value == "Open":
            query = query.where(Issue.status != "Resolved")
            continue
        if value and value not in choices:
            return jsonify(message="Choose a valid filter."), 400
        if value:
            query = query.where(getattr(Issue, field) == value)
    search = request.args.get("q", "").strip()[:120]
    if search:
        query = query.where(
            or_(
                *(
                    getattr(Issue, field).icontains(search, autoescape=True)
                    for field in ("title", "description", "location")
                )
            )
        )
    try:
        page = int(request.args.get("page", "1"))
        if not 1 <= page <= 1000000:
            raise ValueError
    except ValueError:
        return jsonify(message="Invalid page."), 400
    total = db.session.scalar(db.select(func.count()).select_from(query.subquery()))
    rows = db.session.scalars(
        query.order_by(Issue.created_at.desc(), Issue.id.desc())
        .limit(20)
        .offset((page - 1) * 20)
    ).all()
    return jsonify(
        issues=[serialize(row) for row in rows], total=total, page=page, counts=counts
    )


@issues.post("")
@require_role("Resident")
@limiter.limit("20 per minute")
def create_issue():
    data = (
        request.form.to_dict()
        if request.mimetype == "multipart/form-data"
        else request.get_json(silent=True)
    )
    if not isinstance(data, dict):
        return jsonify(message="Enter the report details."), 400
    errors, values = {}, {}
    for field, minimum, maximum in (
        ("title", 1, 100),
        ("description", 0, 1000),
        ("location", 1, 200),
    ):
        value = data.get(field, "")
        if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
            errors[field] = f"Use {minimum}–{maximum} characters."
        else:
            values[field] = value.strip()
    for field, choices in (("category", CATEGORIES), ("priority", PRIORITIES)):
        if field == "priority" and field not in data:
            data[field] = "Normal"
        if data.get(field) not in choices:
            errors[field] = "Choose a valid option."
        else:
            values[field] = data[field]
    if errors:
        return (
            jsonify(message="Please check the highlighted fields.", errors=errors),
            400,
        )
    key = data.get("submission_key")
    if key:
        try:
            key = str(uuid.UUID(key))
        except (ValueError, TypeError, AttributeError):
            return (
                jsonify(message="Invalid report submission. Please reload the form."),
                400,
            )
        existing = db.session.scalar(
            db.select(Issue).where(
                Issue.user_id == g.user.id, Issue.submission_key == key
            )
        )
        if existing:
            return jsonify(issue=serialize(existing)), 201
    files = request.files.getlist("photo")
    if len(files) > 1 or any(field != "photo" for field in request.files):
        return (
            jsonify(
                message="Only one photo per report is supported.",
                errors={"photo": "Choose one photo."},
            ),
            400,
        )
    name = None
    if files:
        try:
            name = save_photo(files[0])
        except ValueError as error:
            return (
                jsonify(
                    message="The photo could not be uploaded.",
                    errors={"photo": str(error)},
                ),
                400,
            )
        except OSError:
            current_app.logger.exception("Photo storage failed")
            return (
                jsonify(
                    message="The photo could not be saved. Please retry or remove it and submit without a photo.",
                    errors={"photo": "Photo storage is temporarily unavailable."},
                ),
                503,
            )
    issue = Issue(
        **values,
        user_id=g.user.id,
        status="Reported",
        photo_name=name,
        submission_key=key or None,
    )
    try:
        db.session.add(issue)
        db.session.flush()
        db.session.add(
            IssueUpdate(
                issue_id=issue.id,
                actor_id=g.user.id,
                status="Reported",
                note="Report submitted.",
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        remove_photo(name)
        if key:
            existing = db.session.scalar(
                db.select(Issue).where(
                    Issue.user_id == g.user.id, Issue.submission_key == key
                )
            )
            if existing:
                return jsonify(issue=serialize(existing)), 201
        raise
    return jsonify(issue=serialize(issue)), 201


@issues.get("/<int:issue_id>")
@require_auth
def detail(issue_id):
    issue = db.session.scalar(visible_query().where(Issue.id == issue_id))
    if not issue:
        return jsonify(message="Report not found."), 404
    updates = db.session.scalars(
        db.select(IssueUpdate)
        .where(IssueUpdate.issue_id == issue.id)
        .order_by(IssueUpdate.created_at, IssueUpdate.id)
    ).all()
    return jsonify(
        issue=serialize(issue),
        updates=[
            {
                "id": row.id,
                "status": row.status,
                "note": row.note,
                "created_at": aware(row.created_at).isoformat(),
            }
            for row in updates
        ],
    )


@issues.patch("/<int:issue_id>")
@require_role("Administrator")
def update_issue(issue_id):
    issue = db.session.scalar(
        db.select(Issue).where(Issue.id == issue_id).with_for_update()
    )
    if not issue:
        return jsonify(message="Report not found."), 404
    data = request.get_json(silent=True)
    if (
        not isinstance(data, dict)
        or data.get("status") not in STATUSES
        or not isinstance(data.get("note"), str)
        or not 5 <= len(data["note"].strip()) <= 1000
    ):
        return (
            jsonify(
                message="Choose a status and add a progress note of 5–1000 characters."
            ),
            400,
        )
    issue.status = data["status"]
    db.session.add(
        IssueUpdate(
            issue_id=issue.id,
            actor_id=g.user.id,
            status=issue.status,
            note=data["note"].strip(),
        )
    )
    db.session.commit()
    return jsonify(issue=serialize(issue))


@issues.get("/<int:issue_id>/photo")
@require_auth
def report_photo(issue_id):
    issue = db.session.scalar(visible_query().where(Issue.id == issue_id))
    if not issue:
        return jsonify(message="Report not found."), 404
    path = photo_path(issue.photo_name)
    if not path or not path.is_file():
        return jsonify(message="Photo unavailable."), 404
    return send_file(
        path, mimetype="image/jpeg", download_name=f"report-{issue.id}.jpg", max_age=0
    )

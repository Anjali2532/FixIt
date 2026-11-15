"""Resident reports and administrator progress updates."""

from flask import Blueprint, current_app, g, jsonify, request, send_file
import uuid
from datetime import timedelta
from .photos import save_photo, remove_photo, photo_path
from sqlalchemy import func, or_

from .extensions import db, limiter
from .models import Issue, IssueUpdate, StaffContact
from .staff import public_contact
from .security.access import require_auth, require_role, aware, utc_now

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
STATUSES = ("Reported", "Assigned", "In Progress", "Resolved")
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
        "assigned_to": public_contact(issue.assigned_to) if issue.assigned_to else None,
        "version": issue.version,
        "updated_at": aware(issue.updated_at).isoformat(),
        **(
            {"reporter": issue.reporter.full_name}
            if g.user.role == "Administrator"
            else {}
        ),
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
    total_all = sum(counts.values())
    attention = or_(
        Issue.assigned_to_id.is_(None), Issue.created_at < utc_now() - timedelta(days=7)
    )
    attention = (Issue.status != "Resolved") & attention
    summary = None
    if g.user.role == "Administrator":
        needs_attention = db.session.scalar(
            db.select(func.count()).select_from(Issue).where(attention)
        )
        categories = db.session.execute(
            db.select(Issue.category, func.count())
            .group_by(Issue.category)
            .order_by(func.count().desc(), Issue.category)
        ).all()
        summary = {
            "needs_attention": needs_attention,
            "categories": [
                {"name": name, "count": count} for name, count in categories
            ],
        }
        assigned = request.args.get("assignee", "")
        if assigned == "unassigned":
            query = query.where(Issue.assigned_to_id.is_(None))
        elif assigned:
            try:
                contact_id = int(assigned)
                if contact_id < 1:
                    raise ValueError
            except ValueError:
                return jsonify(message="Invalid staff filter."), 400
            query = query.where(Issue.assigned_to_id == contact_id)
        if request.args.get("attention") == "1":
            query = query.where(attention)
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
    sort = request.args.get("sort", "newest")
    orders = {
        "newest": Issue.created_at.desc(),
        "oldest": Issue.created_at.asc(),
        "status": Issue.status.asc(),
        "category": Issue.category.asc(),
    }
    if sort not in orders:
        return jsonify(message="Invalid sort option."), 400
    rows = db.session.scalars(
        query.order_by(orders[sort], Issue.id.desc()).limit(20).offset((page - 1) * 20)
    ).all()
    return jsonify(
        issues=[serialize(row) for row in rows],
        total=total,
        total_all=total_all,
        page=page,
        counts=counts,
        summary=summary,
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
                action="Created",
                new_value="Reported",
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
                "action": row.action,
                "old_value": row.old_value,
                "new_value": row.new_value,
                **(
                    {"changed_by": row.actor.full_name}
                    if g.user.role == "Administrator"
                    else {}
                ),
            }
            for row in updates
        ],
    )


def record_change(issue, action, old_value, new_value, note):
    issue.version += 1
    issue.updated_at = utc_now()
    db.session.add(
        IssueUpdate(
            issue_id=issue.id,
            actor_id=g.user.id,
            status=issue.status,
            action=action,
            old_value=old_value,
            new_value=new_value,
            note=note,
        )
    )


def editable_issue(issue_id):
    issue = db.session.scalar(
        db.select(Issue).where(Issue.id == issue_id).with_for_update()
    )
    if not issue:
        return None, (jsonify(message="Report not found."), 404)
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or type(data.get("version")) is not int:
        return None, (jsonify(message="Reload the report before saving."), 400)
    if data["version"] != issue.version:
        return None, (
            jsonify(
                message="This report was just updated. Reload it and review the latest changes before saving.",
                code="REPORT_CHANGED",
            ),
            409,
        )
    return issue, None


@issues.patch("/<int:issue_id>")
@require_role("Administrator")
def update_issue(issue_id):
    issue, error = editable_issue(issue_id)
    if error:
        return error
    data = request.get_json()
    status, note = data.get("status"), data.get("note", "")
    if status not in STATUSES:
        return jsonify(message="Choose a valid status."), 400
    if status == issue.status:
        return jsonify(issue=serialize(issue), message="No status change was needed.")
    if not isinstance(note, str) or not 5 <= len(note.strip()) <= 1000:
        return (
            jsonify(
                message="Add a progress note of 5–1000 characters. Resolution requires a note explaining the fix."
            ),
            400,
        )
    if status in {"Assigned", "In Progress"} and not issue.assigned_to_id:
        return (
            jsonify(
                message="Assign this report to someone before changing its status."
            ),
            400,
        )
    allowed = {
        "Reported": {"Assigned", "Resolved"},
        "Assigned": {"In Progress", "Resolved"},
        "In Progress": {"Resolved"},
        "Resolved": {"In Progress", "Reported"},
    }
    if status not in allowed[issue.status]:
        return (
            jsonify(
                message="That status change is not allowed. Resolve the report or reopen a resolved report first."
            ),
            400,
        )
    old = issue.status
    issue.status = status
    record_change(issue, "StatusChanged", old, status, note.strip())
    db.session.commit()
    return jsonify(issue=serialize(issue), message="Progress update saved.")


@issues.post("/<int:issue_id>/assignment")
@require_role("Administrator")
def assign_issue(issue_id):
    issue, error = editable_issue(issue_id)
    if error:
        return error
    data = request.get_json()
    staff_id, note = data.get("staff_id"), data.get("note", "")
    if (
        type(staff_id) is not int
        or not isinstance(note, str)
        or len(note.strip()) > 1000
    ):
        return (
            jsonify(
                message="Choose a staff member and use a note of at most 1000 characters."
            ),
            400,
        )
    contact = db.session.get(StaffContact, staff_id)
    if not contact or not contact.is_active:
        return jsonify(message="Choose an active staff contact."), 400
    if issue.status == "Resolved":
        return (
            jsonify(message="Reopen this report before changing its assignment."),
            400,
        )
    if issue.assigned_to_id == contact.id:
        return jsonify(
            issue=serialize(issue),
            message="This report is already assigned to that person.",
        )
    old = issue.assigned_to.full_name if issue.assigned_to else None
    issue.assigned_to = contact
    previous_status = issue.status
    if previous_status == "Reported":
        issue.status = "Assigned"
    record_change(
        issue,
        "Reassigned" if old else "Assigned",
        old,
        contact.full_name,
        note.strip() or f"Assigned to {contact.full_name} ({contact.team}).",
    )
    if previous_status != issue.status:
        db.session.add(
            IssueUpdate(
                issue_id=issue.id,
                actor_id=g.user.id,
                status=issue.status,
                action="StatusChanged",
                old_value=previous_status,
                new_value=issue.status,
                note="Assignment accepted.",
            )
        )
    db.session.commit()
    return jsonify(issue=serialize(issue), message="Assignment saved.")


@issues.post("/<int:issue_id>/notes")
@require_role("Administrator")
def add_note(issue_id):
    issue, error = editable_issue(issue_id)
    if error:
        return error
    note = request.get_json().get("note")
    if not isinstance(note, str) or not 5 <= len(note.strip()) <= 1000:
        return jsonify(message="Add a note of 5–1000 characters."), 400
    record_change(issue, "NoteAdded", None, None, note.strip())
    db.session.commit()
    return jsonify(issue=serialize(issue), message="Progress note saved.")


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

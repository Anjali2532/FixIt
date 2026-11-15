from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError

from server.app.extensions import db
from server.app.models import Issue, IssueUpdate, StaffContact
from server.app.security.access import utc_now
from server.tests.test_issues import signup, report, admin


def send(client, method, path, body):
    token = client.get("/api/auth/csrf").json["csrf_token"]
    return getattr(client, method)(path, json=body, headers={"X-CSRFToken": token})


def setup_report(client):
    signup(client)
    issue_id = report(client).json["issue"]["id"]
    admin(client)
    return issue_id


def contact(client, name="Maintenance Tester"):
    result = send(client, "post", "/api/staff", dict(name=name, team="Maintenance"))
    assert result.status_code == 201
    return result.json["contact"]["id"]


def version(client, issue_id):
    return client.get(f"/api/issues/{issue_id}").json["issue"]["version"]


def assign(client, issue_id, staff_id, **values):
    return send(
        client,
        "post",
        f"/api/issues/{issue_id}/assignment",
        dict(staff_id=staff_id, version=version(client, issue_id)) | values,
    )


def status(client, issue_id, value, **values):
    return send(
        client,
        "patch",
        f"/api/issues/{issue_id}",
        dict(
            status=value,
            note="Maintenance progress recorded.",
            version=version(client, issue_id),
        )
        | values,
    )


def test_assignment_reassignment_status_and_resident_history(client, app):
    signup(client)
    issue_id = report(client).json["issue"]["id"]
    manager = app.test_client()
    admin(manager)
    first = contact(manager)
    second = contact(manager, "Second Technician")
    assert assign(manager, issue_id, first).json["issue"]["status"] == "Assigned"
    assert status(manager, issue_id, "In Progress").status_code == 200
    assert assign(manager, issue_id, second).json["issue"]["status"] == "In Progress"
    assert status(manager, issue_id, "Resolved").status_code == 200
    assert assign(manager, issue_id, first).status_code == 400
    assert status(manager, issue_id, "In Progress").status_code == 200
    resident = client.get(f"/api/issues/{issue_id}").json
    assert resident["issue"]["assigned_to"]["name"] == "Second Technician"
    assert all("changed_by" not in row for row in resident["updates"])
    assert "reporter" not in resident["issue"]
    detail = manager.get(f"/api/issues/{issue_id}").json
    reassigned = next(row for row in detail["updates"] if row["action"] == "Reassigned")
    assert reassigned["old_value"] == "Maintenance Tester"
    assert reassigned["new_value"] == "Second Technician"
    assert reassigned["changed_by"] == "Admin"
    assert detail["updates"][-1]["old_value"] == "Resolved"
    assert detail["updates"][-1]["new_value"] == "In Progress"


def test_staff_contact_permissions_and_validation(client, app):
    assert client.get("/api/staff").status_code == 401
    signup(client)
    assert client.get("/api/staff").status_code == 403
    assert (
        send(
            client, "post", "/api/staff", dict(name="Someone", team="Maintenance")
        ).status_code
        == 403
    )
    admin(client)
    for body in [
        [],
        {},
        dict(name="", team="X"),
        dict(name="X", team=""),
        dict(name="X" * 101, team="Y"),
        dict(name=2, team="Y"),
    ]:
        assert send(client, "post", "/api/staff", body).status_code == 400
    staff_id = contact(client)
    assert (
        send(
            client,
            "post",
            "/api/staff",
            dict(name="Maintenance Tester", team="Maintenance"),
        ).status_code
        == 409
    )
    assert (
        send(client, "patch", f"/api/staff/{staff_id}", dict(is_active=False)).json[
            "contact"
        ]["is_active"]
        is False
    )
    assert (
        send(
            client, "patch", f"/api/staff/{staff_id}", dict(is_active="false")
        ).status_code
        == 400
    )
    assert (
        send(client, "patch", "/api/staff/999", dict(is_active=False)).status_code
        == 404
    )
    assert client.post("/api/staff", json={}).json["code"] == "CSRF_FAILED"


@pytest.mark.parametrize("value", ["Assigned", "In Progress"])
def test_assignment_required_before_work(client, value):
    issue_id = setup_report(client)
    assert status(client, issue_id, value).status_code == 400
    assert db.session.get(Issue, issue_id).status == "Reported"


def test_resolution_note_and_no_change_history(client):
    issue_id = setup_report(client)
    assert status(client, issue_id, "Resolved", note=" ").status_code == 400
    assert (
        status(client, issue_id, "Reported", note="No change needed").status_code == 200
    )
    assert db.session.query(IssueUpdate).count() == 1
    assert assign(client, issue_id, contact(client)).status_code == 200
    count = db.session.query(IssueUpdate).count()
    current = version(client, issue_id)
    staff_id = db.session.get(Issue, issue_id).assigned_to_id
    assert assign(client, issue_id, staff_id).status_code == 200
    assert version(client, issue_id) == current
    assert db.session.query(IssueUpdate).count() == count


def test_inactive_or_missing_contact_cannot_receive_assignment(client):
    issue_id = setup_report(client)
    staff_id = contact(client)
    send(client, "patch", f"/api/staff/{staff_id}", dict(is_active=False))
    for value in [staff_id, 999, 0, None, "1", True]:
        assert assign(client, issue_id, value).status_code == 400
    assert db.session.get(Issue, issue_id).assigned_to_id is None


def test_stale_update_and_assignment_return_conflict(client):
    issue_id = setup_report(client)
    staff_id = contact(client)
    original = version(client, issue_id)
    assert assign(client, issue_id, staff_id).status_code == 200
    result = send(
        client,
        "patch",
        f"/api/issues/{issue_id}",
        dict(status="Resolved", note="Completed maintenance.", version=original),
    )
    assert result.status_code == 409
    assert result.json["code"] == "REPORT_CHANGED"
    assert (
        send(
            client,
            "post",
            f"/api/issues/{issue_id}/assignment",
            dict(staff_id=staff_id, version=original),
        ).status_code
        == 409
    )
    assert (
        send(
            client,
            "patch",
            f"/api/issues/{issue_id}",
            dict(status="Resolved", note="Completed maintenance."),
        ).status_code
        == 400
    )
    assert db.session.get(Issue, issue_id).status == "Assigned"


def test_note_only_records_history_and_updates_version(client):
    issue_id = setup_report(client)
    current = version(client, issue_id)
    result = send(
        client,
        "post",
        f"/api/issues/{issue_id}/notes",
        dict(note="Waiting for replacement parts.", version=current),
    )
    assert result.status_code == 200
    assert result.json["issue"]["version"] == current + 1
    assert result.json["issue"]["status"] == "Reported"
    detail = client.get(f"/api/issues/{issue_id}").json
    assert detail["updates"][-1]["action"] == "NoteAdded"
    assert (
        send(
            client,
            "post",
            f"/api/issues/{issue_id}/notes",
            dict(note="X", version=current + 1),
        ).status_code
        == 400
    )


def test_assignment_and_history_rollback_together(client):
    issue_id = setup_report(client)
    staff_id = contact(client)

    def fail(*args):
        raise SQLAlchemyError("Simulated history failure")

    event.listen(IssueUpdate, "before_insert", fail)
    try:
        assert assign(client, issue_id, staff_id).status_code == 503
    finally:
        event.remove(IssueUpdate, "before_insert", fail)
    issue = db.session.get(Issue, issue_id)
    assert issue.status == "Reported"
    assert issue.assigned_to_id is None
    assert issue.version == 1
    assert db.session.query(IssueUpdate).count() == 1


def test_summaries_filters_and_sorting(client):
    signup(client)
    first = report(client, title="Old light issue").json["issue"]["id"]
    second = report(client, title="New plumbing issue", category="Plumbing").json[
        "issue"
    ]["id"]
    db.session.get(Issue, first).created_at = utc_now() - timedelta(days=8)
    db.session.commit()
    admin(client)
    staff_id = contact(client)
    assign(client, first, staff_id)
    result = client.get("/api/issues").json
    assert result["summary"]["needs_attention"] == 2
    assert result["counts"]["Assigned"] == 1
    assert result["total_all"] == 2
    assert result["issues"][0]["reporter"] == "Report Tester"
    assert client.get(f"/api/issues?assignee={staff_id}").json["total"] == 1
    assert client.get("/api/issues?assignee=unassigned").json["total"] == 1
    assert client.get("/api/issues?sort=oldest").json["issues"][0]["id"] == first
    assert (
        client.get("/api/issues?sort=category").json["issues"][0]["category"]
        == "Lighting"
    )
    assert client.get("/api/issues?sort=bad").status_code == 400
    assert client.get("/api/issues?assignee=bad").status_code == 400
    status(client, first, "Resolved")
    assert client.get("/api/issues?attention=1").json["total"] == 1
    assert client.get("/api/issues?status=Open").json["counts"]["Resolved"] == 1
    assert client.get("/api/issues?status=Open").json["total"] == 1


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/issues/1/assignment", "post"),
        ("/api/issues/1/notes", "post"),
        ("/api/staff/1", "patch"),
    ],
)
def test_admin_mutations_block_residents_and_require_csrf(client, path, method):
    signup(client)
    report(client)
    assert (
        send(
            client, method, path, dict(version=1, staff_id=1, note="Unauthorized")
        ).status_code
        == 403
    )
    assert getattr(client, method)(path, json={}).json["code"] == "CSRF_FAILED"


def test_history_and_assignment_endpoints_cannot_edit_or_delete_history(client):
    issue_id = setup_report(client)
    assert client.delete(f"/api/issues/{issue_id}").status_code == 405
    assert client.get("/api/issues/9999").status_code == 404
    assert (
        send(
            client, "post", "/api/issues/9999/assignment", dict(version=1, staff_id=1)
        ).status_code
        == 404
    )
    assert client.get("/api/history/1").status_code == 404


def test_combined_frontend_and_unknown_api(client, app, tmp_path):
    (tmp_path / "index.html").write_text("<html>FixIt production build</html>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/app.js").write_text('console.log("test")')
    app.config["FRONTEND_FOLDER"] = str(tmp_path)
    assert b"FixIt production build" in client.get("/my-reports").data
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/api/does-not-exist").status_code == 404
    assert client.get("/.env").status_code == 404
    assert client.get("/assets/missing.js").status_code == 404
    response = client.get("/")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_production_requires_strong_configuration(monkeypatch):
    from server.app import create_app

    monkeypatch.setenv("FIXIT_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "short")
    with pytest.raises(RuntimeError, match="32 characters"):
        create_app()
    monkeypatch.setenv("SECRET_KEY", "x" * 40)
    monkeypatch.delenv("RATELIMIT_STORAGE_URI", raising=False)
    with pytest.raises(RuntimeError, match="Redis"):
        create_app()


def test_frontend_build_unavailable_has_clear_response(client, app, tmp_path):
    app.config["FRONTEND_FOLDER"] = str(tmp_path)
    assert client.get("/").status_code == 503

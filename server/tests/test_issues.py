import pytest

from server.app.extensions import db
from server.app.models import Issue, IssueUpdate, User
from server.app.security.password import hash_password


def mutate(client, method, path, body):
    token = client.get("/api/auth/csrf").json["csrf_token"]
    return getattr(client, method)(path, json=body, headers={"X-CSRFToken": token})


def signup(client, email="reporter@example.test"):
    result = mutate(
        client,
        "post",
        "/api/auth/register",
        dict(
            name="Report Tester",
            email=email,
            password="Testing123",
            confirm_password="Testing123",
        ),
    )
    assert result.status_code == 201


def report(client, **overrides):
    return mutate(
        client,
        "post",
        "/api/issues",
        dict(
            title="Broken hallway light",
            description="The light beside the second floor stairs does not turn on.",
            location="Building A, second floor",
            category="Electrical",
            priority="High",
        )
        | overrides,
    )


def admin(client):
    user = User(
        full_name="Admin",
        email="admin@example.test",
        role="Administrator",
        password_hash=hash_password("Testing123"),
    )
    db.session.add(user)
    db.session.commit()
    assert (
        mutate(
            client,
            "post",
            "/api/auth/login",
            dict(email=user.email, password="Testing123"),
        ).status_code
        == 200
    )


def test_create_persists_and_ignores_owner_status_injection(client):
    signup(client)
    result = report(client, user_id=999, status="Resolved")
    assert result.status_code == 201
    issue = db.session.get(Issue, result.json["issue"]["id"])
    assert issue.user_id == db.session.scalar(db.select(User.id))
    assert issue.status == "Reported"
    detail = client.get(f"/api/issues/{issue.id}").json
    assert detail["updates"][0]["note"] == "Report submitted."
    assert detail["issue"]["location"] == "Building A, second floor"


@pytest.mark.parametrize(
    "overrides,field",
    [
        ({"title": "a"}, "title"),
        ({"description": "short"}, "description"),
        ({"location": ""}, "location"),
        ({"category": "invalid"}, "category"),
        ({"priority": "Urgent"}, "priority"),
        ({"title": ["bad"]}, "title"),
    ],
)
def test_invalid_report_does_not_save(client, overrides, field):
    signup(client)
    result = report(client, **overrides)
    assert result.status_code == 400
    assert field in result.json["errors"]
    assert db.session.query(Issue).count() == 0


def test_other_resident_cannot_read_or_change_report(client, app):
    signup(client)
    issue_id = report(client).json["issue"]["id"]
    second = app.test_client()
    signup(second, "other@example.test")
    assert second.get("/api/issues").json["total"] == 0
    assert second.get(f"/api/issues/{issue_id}").status_code == 404
    assert (
        mutate(
            second,
            "patch",
            f"/api/issues/{issue_id}",
            dict(status="Resolved", note="Not allowed"),
        ).status_code
        == 403
    )


def test_admin_progress_visible_to_owner_and_history_preserved(client, app):
    signup(client)
    issue_id = report(client).json["issue"]["id"]
    staff = app.test_client()
    admin(staff)
    assert staff.get("/api/issues").json["total"] == 1
    for status in ["In Progress", "Resolved"]:
        assert (
            mutate(
                staff,
                "patch",
                f"/api/issues/{issue_id}",
                dict(status=status, note=f"Work is now {status.lower()}."),
            ).status_code
            == 200
        )
    result = client.get(f"/api/issues/{issue_id}").json
    assert result["issue"]["status"] == "Resolved"
    assert [item["status"] for item in result["updates"]] == [
        "Reported",
        "In Progress",
        "Resolved",
    ]
    assert client.get("/api/issues").json["counts"]["Resolved"] == 1
    assert report(staff).status_code == 403


def test_admin_invalid_update_does_not_change_data(client):
    signup(client)
    issue_id = report(client).json["issue"]["id"]
    admin(client)
    for body in [
        [],
        {},
        dict(status="Unknown", note="A real note"),
        dict(status="Resolved", note=" "),
        dict(status="Resolved", note=123),
    ]:
        assert (
            mutate(client, "patch", f"/api/issues/{issue_id}", body).status_code == 400
        )
    assert db.session.get(Issue, issue_id).status == "Reported"
    assert db.session.query(IssueUpdate).count() == 1


def test_search_filters_and_pagination(client):
    signup(client)
    for i in range(21):
        assert report(client, title=f"Broken hallway light {i}").status_code == 201
    assert (
        report(client, title="Kitchen pipe leaking", category="Plumbing").status_code
        == 201
    )
    assert client.get("/api/issues").json["total"] == 22
    assert len(client.get("/api/issues").json["issues"]) == 20
    assert len(client.get("/api/issues?page=2").json["issues"]) == 2
    assert client.get("/api/issues?q=Kitchen&category=Plumbing").json["total"] == 1
    assert client.get("/api/issues?q=second%20floor").json["total"] == 22
    assert client.get("/api/issues?q=%25").json["total"] == 0
    assert client.get("/api/issues?status=Resolved").json["total"] == 0
    assert client.get("/api/issues?status=Invalid").status_code == 400
    assert client.get("/api/issues?page=invalid").status_code == 400
    assert client.get("/api/issues?page=999999999999999999999").status_code == 400
    assert client.get("/api/issues?page=0").status_code == 400


def test_auth_and_csrf_required(client):
    assert client.get("/api/issues").status_code == 401
    assert client.get("/api/issues/1").status_code == 401
    signup(client)
    assert client.post("/api/issues", json={}).json["code"] == "CSRF_FAILED"
    assert client.patch("/api/issues/1", json={}).json["code"] == "CSRF_FAILED"
    assert mutate(client, "post", "/api/issues", []).status_code == 400
    assert client.get("/api/issues/9999").status_code == 404

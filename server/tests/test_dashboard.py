from datetime import timedelta

import pytest

from server.app.extensions import db
from server.app.models import Issue, User
from server.app.security.access import utc_now
from server.tests.test_issues import signup, admin


def reports_for_sorting(client):
    signup(client)
    owner = db.session.scalar(
        db.select(User).where(User.email == "reporter@example.test")
    )
    now = utc_now()
    reports = []
    for index in range(47):
        issue = Issue(
            user_id=owner.id,
            title=f"Report {index}",
            description="Sorting example",
            location="Hallway",
            category=("Lighting", "Plumbing", "Safety")[index % 3],
            priority="Normal",
            status=("Reported", "Assigned", "In Progress", "Resolved")[index % 4],
            created_at=now - timedelta(days=index // 2),
        )
        db.session.add(issue)
        reports.append(issue)
    db.session.commit()
    return reports


@pytest.mark.parametrize(
    "sort,field,descending",
    [
        ("newest", "created_at", True),
        ("oldest", "created_at", False),
        ("status", "status", False),
        ("status-desc", "status", True),
        ("category", "category", False),
        ("category-desc", "category", True),
    ],
)
def test_sorting_is_consistent_across_pages(client, sort, field, descending):
    reports = reports_for_sorting(client)
    admin(client)
    expected = sorted(reports, key=lambda issue: issue.id, reverse=True)
    expected = sorted(
        expected, key=lambda issue: getattr(issue, field), reverse=descending
    )
    received = []
    for page in range(1, 4):
        response = client.get(f"/api/issues?sort={sort}&page={page}")
        assert response.status_code == 200
        assert response.json["total"] == 47
        received += [issue["id"] for issue in response.json["issues"]]
    assert received == [issue.id for issue in expected]
    assert len(set(received)) == 47


def test_sorting_keeps_filters_and_ownership(client, app):
    reports = reports_for_sorting(client)
    other = app.test_client()
    signup(other, "other@example.test")
    other_id = db.session.scalar(
        db.select(User.id).where(User.email == "other@example.test")
    )
    db.session.add(
        Issue(
            user_id=other_id,
            title="Private report",
            description="",
            location="Hallway",
            category="Lighting",
            priority="Normal",
            status="Reported",
        )
    )
    db.session.commit()
    response = client.get(
        "/api/issues?category=Lighting&status=Reported&sort=category-desc&q=Report"
    )
    expected = [
        issue.id
        for issue in reversed(reports)
        if issue.category == "Lighting" and issue.status == "Reported"
    ]
    assert [issue["id"] for issue in response.json["issues"]] == expected
    assert response.json["total_all"] == 47
    assert other.get("/api/issues?sort=status-desc").json["total_all"] == 1


@pytest.mark.parametrize(
    "value", ["title", "status;DROP TABLE issues", "category desc"]
)
def test_sorting_accepts_only_supported_options(client, value):
    reports_for_sorting(client)
    response = client.get("/api/issues", query_string={"sort": value})
    assert response.status_code == 400
    assert db.session.query(Issue).count() == 47

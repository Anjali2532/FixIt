import pytest
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError

from server.app.extensions import db
from server.app.models import Issue, IssueUpdate, StaffContact, User
from server.tests.test_issues import signup, report, mutate

PASSWORD = "DemoTesting123"


def seed(app, count=100):
    return app.test_cli_runner().invoke(
        args=["seed-demo", "--reports", str(count)], input=f"{PASSWORD}\n{PASSWORD}\n"
    )


def test_sample_reports_have_consistent_owners_and_history(app, client):
    signup(client)
    original = report(client).json["issue"]["id"]
    app.config["ALLOW_DEMO_DATA"] = True
    result = seed(app)
    assert result.exit_code == 0, result.output
    assert PASSWORD not in result.output
    assert db.session.get(Issue, original).title == "Broken hallway light"
    assert db.session.query(Issue).count() == 101
    assert db.session.query(User).count() == 6
    assert db.session.query(StaffContact).count() == 5
    for issue in db.session.scalars(db.select(Issue).where(Issue.id != original)):
        updates = db.session.scalars(
            db.select(IssueUpdate)
            .where(IssueUpdate.issue_id == issue.id)
            .order_by(IssueUpdate.created_at, IssueUpdate.id)
        ).all()
        assert issue.title.startswith("Demo:")
        assert issue.reporter.role == "Resident"
        assert updates[0].action == "Created"
        assert updates[-1].status == issue.status
        assert (
            issue.version
            == {"Reported": 1, "Assigned": 2, "In Progress": 3, "Resolved": 4}[
                issue.status
            ]
        )
        assert (issue.assigned_to_id is None) == (issue.status == "Reported")
    login = mutate(
        client,
        "post",
        "/api/auth/login",
        dict(email="demo.admin1@example.test", password=PASSWORD),
    )
    assert login.status_code == 200
    assert login.json["user"]["role"] == "Administrator"
    result = seed(app)
    assert result.exit_code != 0
    assert "already exist" in result.output
    assert db.session.query(Issue).count() == 101


@pytest.mark.parametrize("production,enabled", [(False, False), (True, True)])
def test_sample_data_is_disabled_unless_local_development(app, production, enabled):
    app.config.update(PRODUCTION=production, ALLOW_DEMO_DATA=enabled)
    result = seed(app, 4)
    assert result.exit_code != 0
    assert "disabled" in result.output
    assert db.session.query(User).count() == 0


def test_sample_data_rejects_remote_database(app):
    app.config.update(
        ALLOW_DEMO_DATA=True,
        SQLALCHEMY_DATABASE_URI="postgresql+psycopg://example@remote.invalid/fixit_db",
    )
    result = seed(app, 4)
    assert result.exit_code != 0
    assert "local database" in result.output
    assert db.session.query(User).count() == 0


def test_sample_data_rolls_back_if_history_cannot_save(app):
    app.config["ALLOW_DEMO_DATA"] = True

    def fail(*args):
        raise SQLAlchemyError("Simulated sample history failure")

    event.listen(IssueUpdate, "before_insert", fail)
    try:
        result = seed(app, 4)
    finally:
        event.remove(IssueUpdate, "before_insert", fail)
    assert result.exit_code != 0
    assert "rolled back" in result.output
    assert db.session.query(User).count() == 0
    assert db.session.query(StaffContact).count() == 0
    assert db.session.query(Issue).count() == 0


def test_sample_data_rejects_invalid_count_and_password(app):
    app.config["ALLOW_DEMO_DATA"] = True
    assert seed(app, 201).exit_code != 0
    result = app.test_cli_runner().invoke(args=["seed-demo"], input="short\nshort\n")
    assert result.exit_code != 0
    assert db.session.query(User).count() == 0

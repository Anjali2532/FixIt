from flask_migrate import upgrade

from server.app import create_app
from server.app.extensions import db
from server.app.models import Issue, IssueUpdate, User
from server.app.security.access import utc_now
from server.app.security.password import hash_password
from server.tests.test_issues import signup, report


def test_real_migrations_preserve_records_and_allow_new_defaults(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///"
            + str(tmp_path / "migration.sqlite"),
            "RATELIMIT_ENABLED": False,
            "ALLOW_DEMO_DATA": True,
        }
    )
    with app.app_context():
        upgrade(revision="f307c91d5e24")
        created = utc_now()
        owner = User(
            full_name="Earlier Resident",
            email="earlier@example.test",
            password_hash=hash_password("Testing123"),
            created_at=created,
        )
        db.session.add(owner)
        db.session.flush()
        issue = Issue(
            user_id=owner.id,
            title="Earlier report",
            description="Keep this record",
            location="Building A",
            category="Lighting",
            priority="Normal",
            status="Reported",
            created_at=created,
        )
        db.session.add(issue)
        db.session.flush()
        db.session.add(
            IssueUpdate(
                issue_id=issue.id,
                actor_id=owner.id,
                status="Reported",
                note="Report submitted.",
                created_at=created,
            )
        )
        db.session.commit()
        owner_id, issue_id = owner.id, issue.id
        db.session.remove()
        upgrade()
        assert db.session.get(User, owner_id).full_name == "Earlier Resident"
        assert db.session.get(Issue, issue_id).description == "Keep this record"
        assert db.session.query(IssueUpdate).count() == 1
        client = app.test_client()
        signup(client)
        result = report(client)
        assert result.status_code == 201
        new_id = result.json["issue"]["id"]
        assert db.session.get(Issue, new_id).created_at is not None
        history = db.session.scalar(
            db.select(IssueUpdate).where(IssueUpdate.issue_id == new_id)
        )
        assert history.created_at is not None
        result = app.test_cli_runner().invoke(
            args=["seed-demo", "--reports", "4"],
            input="DemoTesting123\nDemoTesting123\n",
        )
        assert result.exit_code == 0, result.output
        assert db.session.query(Issue).count() == 6
        db.session.remove()
        db.engine.dispose()

from flask_migrate import downgrade, upgrade
from sqlalchemy import text

from server.app import create_app
from server.app.extensions import db


def test_photo_migration_preserves_existing_report(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'migration.db'}",
            "RATELIMIT_ENABLED": False,
        }
    )
    with app.app_context():
        upgrade(revision="db260a31f793")
        db.session.execute(
            text(
                "INSERT INTO users (id,full_name,email,password_hash,role,created_at) VALUES (1,'Existing Resident','old@example.test','not-a-real-password','Resident',CURRENT_TIMESTAMP)"
            )
        )
        db.session.execute(
            text(
                "INSERT INTO issues (id,user_id,title,description,location,category,priority,status,created_at) VALUES (1,1,'Old report','Keep this description','Building A','Electrical','Normal','Reported',CURRENT_TIMESTAMP)"
            )
        )
        db.session.commit()
        upgrade()
        row = db.session.execute(
            text("SELECT title,description,category,photo_name FROM issues WHERE id=1")
        ).one()
        assert tuple(row) == ("Old report", "Keep this description", "Lighting", None)
        db.session.remove()
        downgrade(revision="db260a31f793")
        assert (
            db.session.execute(
                text("SELECT description FROM issues WHERE id=1")
            ).scalar_one()
            == "Keep this description"
        )
        db.session.remove()
        upgrade()
        assert (
            db.session.execute(
                text("SELECT photo_name FROM issues WHERE id=1")
            ).scalar_one()
            is None
        )
        db.session.remove()

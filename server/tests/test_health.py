from sqlalchemy.exc import SQLAlchemyError

from server.app.extensions import db


def test_health_does_not_depend_on_database(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise SQLAlchemyError("private connection information")

    monkeypatch.setattr(db.session, "execute", unavailable)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_ready_checks_database(client):
    response = client.get("/api/ready")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "database": "connected"}


def test_ready_returns_safe_error(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise SQLAlchemyError("password=private")

    monkeypatch.setattr(db.session, "execute", unavailable)
    response = client.get("/api/ready")
    assert response.status_code == 503
    assert response.json == {"status": "unavailable", "database": "unavailable"}
    assert "private" not in response.text


def test_database_cli(app):
    result = app.test_cli_runner().invoke(args=["db-check"])
    assert result.exit_code == 0
    assert "successful" in result.output

import os

import pytest
from sqlalchemy.engine import make_url

from server.app import create_app
from server.app.extensions import db


@pytest.fixture
def app():
    url = os.environ.get("FIXIT_TEST_DATABASE_URL", "sqlite:///:memory:")
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite" and (
        parsed.database != "fixit_test" or parsed.host not in {"127.0.0.1", "localhost"}
    ):
        raise RuntimeError("Tests may only reset the local fixit_test database.")
    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": url, "RATELIMIT_ENABLED": False}
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

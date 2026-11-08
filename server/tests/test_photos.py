from io import BytesIO
from pathlib import Path
import uuid

from PIL import Image
import pytest
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError

from server.app.extensions import db
from server.app.models import Issue, IssueUpdate
from server.tests.test_issues import signup, report, admin, mutate


def image_bytes(format="PNG"):
    output = BytesIO()
    Image.new("RGB", (80, 60), "green").save(output, format=format)
    return output.getvalue()


def upload(client, content=None, filename="photo.png", **overrides):
    token = client.get("/api/auth/csrf").json["csrf_token"]
    data = (
        dict(
            title="Hallway light",
            location="Building A",
            category="Lighting",
            description="",
            priority="Normal",
        )
        | overrides
    )
    if content is not None:
        data["photo"] = (BytesIO(content), filename)
    return client.post(
        "/api/issues",
        data=data,
        content_type="multipart/form-data",
        headers={"X-CSRFToken": token},
    )


@pytest.mark.parametrize("format", ["JPEG", "PNG", "WEBP"])
def test_photo_upload_and_access(client, app, format):
    signup(client)
    response = upload(client, image_bytes(format))
    assert response.status_code == 201
    url = response.json["issue"]["photo_url"]
    photo = client.get(url)
    assert photo.status_code == 200
    assert photo.mimetype == "image/jpeg"
    assert photo.headers["Cache-Control"] == "no-store"
    assert photo.headers["X-Content-Type-Options"] == "nosniff"
    with Image.open(BytesIO(photo.data)) as image:
        assert image.size == (80, 60)
        assert not image.getexif()
    other = app.test_client()
    assert other.get(url).status_code == 401
    signup(other, "different@example.test")
    assert other.get(url).status_code == 404
    staff = app.test_client()
    admin(staff)
    assert staff.get(url).status_code == 200


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"<svg><script>alert(1)</script></svg>",
        b"not an image",
        image_bytes("GIF"),
        image_bytes()[:30],
    ],
)
def test_invalid_image_rejected_without_report_or_file(client, app, content):
    signup(client)
    response = upload(client, content)
    assert response.status_code == 400
    assert "photo" in response.json["errors"]
    assert db.session.query(Issue).count() == 0
    assert not list(Path(app.config["UPLOAD_FOLDER"]).glob("*"))


def test_five_mb_limit_and_total_request_limit(client):
    signup(client)
    response = upload(client, b"x" * (5 * 1024 * 1024 + 1))
    assert response.status_code == 400
    assert "5 MB" in response.json["errors"]["photo"]
    response = upload(client, b"x" * (7 * 1024 * 1024))
    assert response.status_code == 413
    assert response.is_json


def test_pixel_limit(client):
    signup(client)
    output = BytesIO()
    Image.new("RGB", (5000, 4100), "white").save(output, format="PNG")
    result = upload(client, output.getvalue())
    assert result.status_code == 400
    assert "pixels" in result.json["errors"]["photo"]


def test_generated_names_and_multiple_photos(client, app):
    signup(client)
    result = upload(client, image_bytes(), filename="../../outside.html")
    assert result.status_code == 201
    files = list(Path(app.config["UPLOAD_FOLDER"]).iterdir())
    assert len(files) == 1
    assert len(files[0].name) == 36
    assert files[0].suffix == ".jpg"
    token = client.get("/api/auth/csrf").json["csrf_token"]
    result = client.post(
        "/api/issues",
        data=dict(
            title="Light",
            location="Hallway",
            category="Lighting",
            photo=[
                (BytesIO(image_bytes()), "one.png"),
                (BytesIO(image_bytes()), "two.png"),
            ],
        ),
        headers={"X-CSRFToken": token},
    )
    assert result.status_code == 400
    assert db.session.query(Issue).count() == 1


def test_missing_photo_file_returns_safe_404(client, app):
    signup(client)
    result = upload(client, image_bytes())
    url = result.json["issue"]["photo_url"]
    for path in Path(app.config["UPLOAD_FOLDER"]).iterdir():
        path.unlink()
    assert client.get(url).status_code == 404
    assert client.get("/api/issues/1").status_code == 200


def test_optional_description_and_photo_and_field_limits(client):
    signup(client)
    result = upload(client, title="A", location="B")
    assert result.status_code == 201
    assert result.json["issue"]["photo_url"] is None
    assert result.json["issue"]["description"] == ""
    assert (
        client.get(f"/api/issues/{result.json['issue']['id']}/photo").status_code == 404
    )
    for values in [
        dict(title="x" * 101),
        dict(description="x" * 1001),
        dict(location=" " * 3),
    ]:
        assert upload(client, **values).status_code == 400


def test_retry_does_not_duplicate_report_or_photo(client, app):
    signup(client)
    key = str(uuid.uuid4())
    first = upload(client, image_bytes(), submission_key=key)
    second = upload(client, image_bytes(), submission_key=key)
    assert first.status_code == second.status_code == 201
    assert first.json["issue"]["id"] == second.json["issue"]["id"]
    assert db.session.query(Issue).count() == 1
    assert db.session.query(IssueUpdate).count() == 1
    assert len(list(Path(app.config["UPLOAD_FOLDER"]).iterdir())) == 1
    assert upload(client, submission_key="bad").status_code == 400


def test_photo_storage_failure_preserves_no_partial_report(client, app, monkeypatch):
    signup(client)

    def fail(*args, **kwargs):
        raise OSError("Simulated full disk")

    monkeypatch.setattr("server.app.issues.save_photo", fail)
    result = upload(client, image_bytes())
    assert result.status_code == 503
    assert db.session.query(Issue).count() == 0
    assert upload(client).status_code == 201


def test_database_failure_removes_uploaded_file(client, app):
    signup(client)

    def fail(*args):
        raise SQLAlchemyError("Simulated history failure")

    event.listen(IssueUpdate, "before_insert", fail)
    try:
        result = upload(client, image_bytes())
        assert result.status_code == 503
        assert db.session.query(Issue).count() == 0
        assert not list(Path(app.config["UPLOAD_FOLDER"]).iterdir())
    finally:
        event.remove(IssueUpdate, "before_insert", fail)


def test_photo_requires_csrf(client):
    signup(client)
    result = client.post(
        "/api/issues", data={"photo": (BytesIO(image_bytes()), "photo.png")}
    )
    assert result.status_code == 400
    assert result.json["code"] == "CSRF_FAILED"


def test_open_filter_and_categories(client):
    signup(client)
    for category in [
        "Lighting",
        "Roads & Sidewalks",
        "Trash & Recycling",
        "Plumbing",
        "Equipment & Facilities",
        "Safety",
        "Other",
    ]:
        assert upload(client, category=category).status_code == 201
    assert client.get("/api/issues?status=Open").json["total"] == 7
    assert client.get("/api/issues?category=Lighting").json["total"] == 1


def test_user_text_is_returned_as_data(client):
    signup(client)
    result = upload(
        client, title="<script>alert(1)</script>", location="'; DROP TABLE issues; --"
    )
    assert result.status_code == 201
    assert client.get("/api/issues?q=%3Cscript%3E").json["total"] == 1
    assert db.session.query(Issue).count() == 1

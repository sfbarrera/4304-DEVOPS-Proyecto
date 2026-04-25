import json
import pytest
from app import create_app
from extensions import db
from flask_jwt_extended import create_access_token


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "test-secret"

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity="test-client")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"


# ── POST /blacklists ──────────────────────────────────────────────────────────

def test_post_blacklist_success(client, auth_headers):
    payload = {
        "email": "bad@example.com",
        "app_uuid": VALID_UUID,
        "blocked_reason": "Spam complaints",
    }
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))

    assert resp.status_code == 201
    data = resp.get_json()
    assert "id" in data
    assert "bad@example.com" in data["msg"]


def test_post_blacklist_without_reason(client, auth_headers):
    payload = {"email": "noreason@example.com", "app_uuid": VALID_UUID}
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 201


def test_post_blacklist_duplicate(client, auth_headers):
    payload = {"email": "dup@example.com", "app_uuid": VALID_UUID}
    client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))

    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))

    assert resp.status_code == 409
    assert "already" in resp.get_json()["msg"].lower()


def test_post_blacklist_invalid_uuid(client, auth_headers):
    payload = {"email": "x@example.com", "app_uuid": "not-a-uuid"}
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 400


def test_post_blacklist_invalid_email(client, auth_headers):
    payload = {"email": "not-an-email", "app_uuid": VALID_UUID}
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 400


def test_post_blacklist_reason_too_long(client, auth_headers):
    payload = {
        "email": "long@example.com",
        "app_uuid": VALID_UUID,
        "blocked_reason": "x" * 256,
    }
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 400


def test_post_blacklist_missing_email(client, auth_headers):
    payload = {"app_uuid": VALID_UUID}
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 400


def test_post_blacklist_missing_app_uuid(client, auth_headers):
    payload = {"email": "x@example.com"}
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 400


def test_post_blacklist_empty_body(client, auth_headers):
    resp = client.post("/blacklists", headers=auth_headers, data="")
    assert resp.status_code == 400


def test_post_blacklist_no_token(client):
    payload = {"email": "noauth@example.com", "app_uuid": VALID_UUID}
    resp = client.post(
        "/blacklists",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 401


def test_post_blacklist_invalid_token(client):
    payload = {"email": "badtoken@example.com", "app_uuid": VALID_UUID}
    headers = {
        "Authorization": "Bearer not.a.real.jwt",
        "Content-Type": "application/json",
    }
    resp = client.post("/blacklists", headers=headers, data=json.dumps(payload))
    assert resp.status_code in (401, 422)


# ── GET /blacklists/<email> ───────────────────────────────────────────────────

def test_get_blacklisted_email(client, auth_headers):
    payload = {
        "email": "check@example.com",
        "app_uuid": VALID_UUID,
        "blocked_reason": "Fraud",
    }
    client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))

    resp = client.get("/blacklists/check@example.com", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["blacklisted"] is True
    assert data["email"] == "check@example.com"
    assert data["blocked_reason"] == "Fraud"
    assert "created_at" in data


def test_get_non_blacklisted_email(client, auth_headers):
    resp = client.get("/blacklists/clean@example.com", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["blacklisted"] is False
    assert data["blocked_reason"] is None


def test_get_blacklist_no_token(client):
    resp = client.get("/blacklists/noauth@example.com")
    assert resp.status_code == 401


# ── GET /health ───────────────────────────────────────────────────────────────

def test_health_check_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_health_check_no_auth_required(client):
    resp = client.get("/health")
    assert resp.status_code == 200

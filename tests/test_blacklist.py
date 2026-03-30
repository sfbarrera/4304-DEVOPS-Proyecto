import pytest
import json
from app import create_app
from extensions import db
from flask_jwt_extended import create_access_token


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


@pytest.fixture
def auth_headers(client):
    with client.application.app_context():
        token = create_access_token(identity="test-client")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── POST /blacklists ──────────────────────────────────────────────────────────

def test_add_email_success(client, auth_headers):
    payload = {
        "email": "bad@example.com",
        "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "blocked_reason": "Spam complaints",
    }
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 201
    data = resp.get_json()
    assert "id" in data
    assert "bad@example.com" in data["msg"]


def test_add_email_no_reason(client, auth_headers):
    payload = {
        "email": "noreasontest@example.com",
        "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
    }
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 201


def test_add_email_duplicate(client, auth_headers):
    payload = {
        "email": "dup@example.com",
        "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
    }
    client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 409


def test_add_email_invalid_uuid(client, auth_headers):
    payload = {"email": "x@example.com", "app_uuid": "not-a-uuid"}
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 400


def test_add_email_reason_too_long(client, auth_headers):
    payload = {
        "email": "long@example.com",
        "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "blocked_reason": "x" * 256,
    }
    resp = client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))
    assert resp.status_code == 400


def test_add_email_no_token(client):
    payload = {"email": "noauth@example.com", "app_uuid": "550e8400-e29b-41d4-a716-446655440000"}
    resp = client.post("/blacklists", data=json.dumps(payload),
                       content_type="application/json")
    assert resp.status_code == 401


# ── GET /blacklists/<email> ───────────────────────────────────────────────────

def test_query_blacklisted_email(client, auth_headers):
    payload = {
        "email": "check@example.com",
        "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "blocked_reason": "Fraud",
    }
    client.post("/blacklists", headers=auth_headers, data=json.dumps(payload))

    resp = client.get("/blacklists/check@example.com", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["blacklisted"] is True
    assert data["blocked_reason"] == "Fraud"


def test_query_non_blacklisted_email(client, auth_headers):
    resp = client.get("/blacklists/clean@example.com", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["blacklisted"] is False
    assert data["blocked_reason"] is None


def test_query_no_token(client):
    resp = client.get("/blacklists/noauth@example.com")
    assert resp.status_code == 401


# ── Health check ──────────────────────────────────────────────────────────────

def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "healthy"

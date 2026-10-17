import uuid

import pytest

from app.extensions import db
from app.models import BlacklistEntry

APP_UUID = str(uuid.uuid4())


@pytest.fixture
def auth():
    return {"Authorization": "Bearer test-static-token"}


def post(client, payload, headers=None, **kwargs):
    return client.post("/blacklists", json=payload, headers=headers, **kwargs)


def test_add_email(client, auth):
    resp = post(
        client,
        {"email": "User@Example.com", "app_uuid": APP_UUID, "blocked_reason": "spam"},
        auth,
        environ_base={"REMOTE_ADDR": "203.0.113.7"},
    )
    assert resp.status_code == 201
    assert "user@example.com" in resp.get_json()["message"]

    with client.application.app_context():
        entry = db.session.execute(db.select(BlacklistEntry)).scalar_one()
        assert entry.email == "user@example.com"
        assert str(entry.app_uuid) == APP_UUID
        assert entry.blocked_reason == "spam"
        assert entry.ip_address == "203.0.113.7"
        assert entry.created_at is not None


def test_client_ip_from_proxy_header(client, auth):
    resp = post(
        client,
        {"email": "a@example.com", "app_uuid": APP_UUID},
        {**auth, "X-Forwarded-For": "198.51.100.4"},
    )
    assert resp.status_code == 201
    with client.application.app_context():
        assert db.session.execute(db.select(BlacklistEntry.ip_address)).scalar_one() == "198.51.100.4"


def test_blocked_reason_is_optional(client, auth):
    resp = post(client, {"email": "a@example.com", "app_uuid": APP_UUID}, auth)
    assert resp.status_code == 201


def test_duplicate_email(client, auth):
    payload = {"email": "a@example.com", "app_uuid": APP_UUID}
    assert post(client, payload, auth).status_code == 201
    resp = post(client, {**payload, "email": "A@example.com"}, auth)
    assert resp.status_code == 409


@pytest.mark.parametrize(
    "payload, field",
    [
        ({"app_uuid": APP_UUID}, "email"),
        ({"email": "not-an-email", "app_uuid": APP_UUID}, "email"),
        ({"email": "a@example.com"}, "app_uuid"),
        ({"email": "a@example.com", "app_uuid": "123"}, "app_uuid"),
        ({"email": "a@example.com", "app_uuid": APP_UUID, "blocked_reason": "x" * 256}, "blocked_reason"),
    ],
)
def test_invalid_payload(client, auth, payload, field):
    resp = post(client, payload, auth)
    assert resp.status_code == 400
    assert field in resp.get_json()["errors"]


def test_requires_token(client):
    resp = post(client, {"email": "a@example.com", "app_uuid": APP_UUID})
    assert resp.status_code == 401


def test_rejects_invalid_token(client):
    resp = post(client, {"email": "a@example.com", "app_uuid": APP_UUID}, {"Authorization": "Bearer nope"})
    assert resp.status_code == 401


def test_get_blacklisted_email(client, auth):
    post(client, {"email": "a@example.com", "app_uuid": APP_UUID, "blocked_reason": "spam"}, auth)
    resp = client.get("/blacklists/A@Example.com", headers=auth)
    assert resp.status_code == 200
    assert resp.get_json() == {"blacklisted": True, "blocked_reason": "spam"}


def test_get_blacklisted_email_without_reason(client, auth):
    post(client, {"email": "a@example.com", "app_uuid": APP_UUID}, auth)
    resp = client.get("/blacklists/a@example.com", headers=auth)
    assert resp.get_json() == {"blacklisted": True, "blocked_reason": None}


def test_get_email_not_blacklisted(client, auth):
    resp = client.get("/blacklists/nobody@example.com", headers=auth)
    assert resp.status_code == 200
    assert resp.get_json() == {"blacklisted": False, "blocked_reason": None}


@pytest.mark.parametrize("headers", [None, {"Authorization": "Bearer nope"}, {"Authorization": "test-static-token"}])
def test_get_requires_token(client, headers):
    resp = client.get("/blacklists/a@example.com", headers=headers)
    assert resp.status_code == 401

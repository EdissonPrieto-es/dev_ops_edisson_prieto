import socket

from app.resources import health


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {
        "status": "ok",
        "database": "ok",
        "version": "dev",
        "instance": socket.gethostname(),
    }


def test_health_reports_bundle_version(client, tmp_path, monkeypatch):
    version_file = tmp_path / "VERSION"
    version_file.write_text("v3\n")
    monkeypatch.setattr(health, "VERSION_FILE", version_file)

    assert client.get("/health").get_json()["version"] == "v3"


def test_health_without_database():
    from app import create_app
    from app.config import TestConfig

    class NoDBConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = "postgresql://x:y@127.0.0.1:5999/none"

    resp = create_app(NoDBConfig).test_client().get("/health")
    assert resp.status_code == 503
    body = resp.get_json()
    assert body["status"] == "degraded"
    assert body["database"] == "unreachable"
    assert body["version"] == "dev"

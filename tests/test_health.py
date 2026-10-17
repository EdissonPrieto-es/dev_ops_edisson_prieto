def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "database": "ok"}


def test_health_without_database():
    from app import create_app
    from app.config import TestConfig

    class NoDBConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = "postgresql://x:y@127.0.0.1:5999/none"

    resp = create_app(NoDBConfig).test_client().get("/health")
    assert resp.status_code == 503
    assert resp.get_json() == {"status": "degraded", "database": "unreachable"}

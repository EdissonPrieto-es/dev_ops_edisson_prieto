from sqlalchemy.engine import make_url

from app.config import _database_url

RDS_ENV = {
    "RDS_HOSTNAME": "db.example.rds.amazonaws.com",
    "RDS_PORT": "5432",
    "RDS_DB_NAME": "ebdb",
    "RDS_USERNAME": "admin",
    "RDS_PASSWORD": "p@ss:w/rd#1",
}


def test_database_url_from_rds_vars(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for key, value in RDS_ENV.items():
        monkeypatch.setenv(key, value)

    url = make_url(_database_url())
    assert url.host == "db.example.rds.amazonaws.com"
    assert url.database == "ebdb"
    assert url.password == "p@ss:w/rd#1"


def test_database_url_takes_precedence(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host:5432/db")
    monkeypatch.setenv("RDS_HOSTNAME", "ignored")
    assert _database_url() == "postgresql://u:p@host:5432/db"

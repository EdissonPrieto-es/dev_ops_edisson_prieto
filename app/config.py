import os
from datetime import timedelta

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()


def _database_url():
    if not os.getenv("DATABASE_URL") and os.getenv("RDS_HOSTNAME"):
        return URL.create(
            "postgresql",
            username=os.environ["RDS_USERNAME"],
            password=os.environ["RDS_PASSWORD"],
            host=os.environ["RDS_HOSTNAME"],
            port=int(os.getenv("RDS_PORT", "5432")),
            database=os.environ["RDS_DB_NAME"],
        ).render_as_string(hide_password=False)

    url = os.getenv("DATABASE_URL", "postgresql://app_user:app_password@localhost:5432/app_db")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    API_TOKEN = os.getenv("API_TOKEN", "dev-static-token")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
    )
    PROPAGATE_EXCEPTIONS = True


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    API_TOKEN = "test-static-token"
    JWT_SECRET_KEY = "test-jwt-secret-key-with-at-least-32-bytes"

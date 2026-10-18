import socket
from pathlib import Path

from flask_restful import Resource
from sqlalchemy import text

from ..extensions import db

# Written into the deployment bundle so each Elastic Beanstalk version is distinguishable.
VERSION_FILE = Path(__file__).resolve().parents[2] / "VERSION"


def _version():
    return VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else "dev"


class HealthResource(Resource):
    def get(self):
        info = {"version": _version(), "instance": socket.gethostname()}
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "ok", "database": "ok", **info}, 200
        except Exception:
            return {"status": "degraded", "database": "unreachable", **info}, 503

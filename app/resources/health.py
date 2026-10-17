from flask_restful import Resource
from sqlalchemy import text

from ..extensions import db


class HealthResource(Resource):
    def get(self):
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "ok", "database": "ok"}, 200
        except Exception:
            return {"status": "degraded", "database": "unreachable"}, 503

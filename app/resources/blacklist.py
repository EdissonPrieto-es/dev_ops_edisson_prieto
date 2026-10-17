from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import BlacklistEntry
from ..schemas import BlacklistCreateSchema

create_schema = BlacklistCreateSchema()


class BlacklistResource(Resource):
    @jwt_required()
    def post(self):
        try:
            data = create_schema.load(request.get_json(silent=True) or {})
        except ValidationError as err:
            return {"message": "Datos inválidos", "errors": err.messages}, 400

        entry = BlacklistEntry(**data, ip_address=request.remote_addr or "unknown")
        db.session.add(entry)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"message": f"El email {data['email']} ya está en la lista negra global"}, 409

        return {"message": f"El email {data['email']} fue agregado a la lista negra global"}, 201

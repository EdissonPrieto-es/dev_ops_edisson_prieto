from marshmallow import fields, pre_load, validate

from ..extensions import ma


class BlacklistCreateSchema(ma.Schema):
    email = fields.Email(required=True)
    app_uuid = fields.UUID(required=True)
    blocked_reason = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=255))

    @pre_load
    def normalize_email(self, data, **kwargs):
        if isinstance(data, dict) and isinstance(data.get("email"), str):
            data = {**data, "email": data["email"].strip().lower()}
        return data

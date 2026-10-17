import hmac
from functools import wraps

from flask import current_app, request


def token_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        expected = current_app.config["API_TOKEN"]
        if scheme.lower() != "bearer" or not hmac.compare_digest(token.strip(), expected):
            return {"message": "Token de autorización inválido o ausente"}, 401
        return view(*args, **kwargs)

    return wrapper

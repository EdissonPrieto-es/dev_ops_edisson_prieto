import click
from flask import Flask
from flask_jwt_extended import create_access_token
from flask_restful import Api
from sqlalchemy.exc import OperationalError
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import db, jwt, ma


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)

    from .resources import register_resources

    api = Api(app)
    register_resources(api)

    with app.app_context():
        from . import models
        try:
            db.create_all()
        except OperationalError:
            app.logger.exception("No se pudo conectar a la base de datos al iniciar")

    @app.cli.command("create-token")
    @click.argument("identity")
    def create_token(identity):
        click.echo(create_access_token(identity=identity, expires_delta=False))

    return app

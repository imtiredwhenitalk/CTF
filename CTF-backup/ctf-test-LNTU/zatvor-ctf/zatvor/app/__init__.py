from flask import Flask

from . import challenge, db, routes
from .config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    app.register_blueprint(routes.bp)
    challenge.init_app(app)

    return app

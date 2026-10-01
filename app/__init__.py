from flask import Flask

from app.routes import api, views


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(views)
    app.register_blueprint(api)
    return app

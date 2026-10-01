"""Forensic Attack Timeline Reconstructor - Flask application factory."""

from flask import Flask

from app.routes import api, views
from app.services import IncidentCase


def create_app() -> Flask:
    app = Flask(__name__)
    app.extensions["incident_case"] = IncidentCase("IR-2026-0914 · Andes Freight Co.")
    app.register_blueprint(views)
    app.register_blueprint(api)
    return app

from flask import Flask

from macroflask.api import api_bp


def create_app():
    app = Flask(__name__)

    app.register_blueprint(api_bp, url_prefix="/api/v1.0")

    return app

from flask import Flask
from config import get_config
from macroflask.models import Base, db
from macroflask.api import api_bp


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False  # disable url redirect ex)'user' and 'user/'
    print(get_config())
    app.config.from_object(get_config())

    # init model

    db_config_dict = {
        'database1': {
            'url': get_config().DATABASE_URI,
            "model_class": Base,
            "engine_options": {},
            "session_options": {}
        }
    }
    db.init_flask_app(app, db_config_dict)

    # init api
    app.register_blueprint(api_bp, url_prefix="/api/v1.0")

    return app

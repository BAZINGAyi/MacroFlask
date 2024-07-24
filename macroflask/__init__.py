import multiprocessing
import os

from flask import Flask
from config import get_config
from macroflask.models import Base, db
from macroflask.api import api_bp
from macroflask.util.light_logging import MacroFlaskLogger

app_logger = None
sys_logger = None


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False  # disable url redirect ex)'user' and 'user/'
    print(get_config())
    app.config.from_object(get_config())

    # init logging
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    logging_manager = MacroFlaskLogger(get_config().LOGGING, app, path=log_dir)
    global app_logger, sys_logger
    app_logger = logging_manager.get_logger("app")
    sys_logger = logging_manager.get_logger("sys")

    # init model
    db_config_dict = {
        'database1': {
            'url': get_config().DATABASE_URI,
            "model_class": Base,
            "engine_options": {},
            "session_options": {}
        }
    }
    db.set_logger(sys_logger)
    db.init_flask_app(app, db_config_dict)

    # init api
    app.register_blueprint(api_bp, url_prefix="/api/v1.0")

    return app
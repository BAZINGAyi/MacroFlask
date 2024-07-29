import os
from flask import Flask
from config import get_config
from macroflask.models import Base, db
from macroflask.api import api_bp
from macroflask.system.rest_mgmt import ResponseHandler
from macroflask.system.extensions import jwt_manager, logging_manager, sys_logger
from macroflask.system.sys_api import system_api_bp


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False  # disable url redirect ex)'user' and 'user/'
    print(get_config())
    app.config.from_object(get_config())

    # init flask internal error response
    @app.errorhandler(500)
    def internal_error(error):
        return ResponseHandler.error("Internal server error", status_code=500)

    @app.errorhandler(404)
    def not_found_error(error):
        return ResponseHandler.error("Resource not found", status_code=404)

    # init logging
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    logging_manager.init_flask_logger(get_config().LOGGING, app, path=log_dir)

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
    # Base.metadata.create_all(db.bind_model_engines[Base])

    # jwt config
    jwt_manager.init_app(app)
    app.config['JWT_SECRET_KEY'] = 'ZZZZ'

    # init api
    app.register_blueprint(api_bp, url_prefix="/api/v1.0")
    app.register_blueprint(system_api_bp, url_prefix="/api/v1.0/system")

    return app
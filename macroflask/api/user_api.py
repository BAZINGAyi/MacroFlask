from flask import abort
from jinja2 import TemplateNotFound
from . import api_bp
from ..models import db
from ..models.user_model import User
from ..service.global_service import app_logger


@api_bp.route('/user/')
def show():
    try:
        username = ""
        with db.get_db_session() as session:
            user = session.query(User).where().first()
            username = user.username
            app_logger.info("User: %s", username)

        return "Hello, World!" + str(12222) + username
    except TemplateNotFound:
        abort(404)
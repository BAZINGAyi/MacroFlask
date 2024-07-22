from flask import abort
from jinja2 import TemplateNotFound
from . import api_bp
from ..models import db
from ..models.user_model import User


@api_bp.route('/user/')
def show():
    try:
        username = ""
        with db.get_db_session() as session:
            user = session.query(User).where().first()
            username = user.username

        return "Hello, World!" + str(12222) + username
    except TemplateNotFound:
        abort(404)
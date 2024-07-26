from flask import abort
from flask_jwt_extended import jwt_required
from jinja2 import TemplateNotFound
from . import api_bp
from macroflask.models import db
from macroflask.system.user_model import User, PermissionsConstant, RoleModulePermission, \
    ModuleConstant
from ..service.global_service import app_logger
from ..system import permission_required


@api_bp.route('/user/')
@jwt_required()
@permission_required(module_id=ModuleConstant.USER, permission_bitmask=PermissionsConstant.READ)
def show():
    try:
        with db.get_db_session() as session:
            user = session.query(User).where().first()
            username = user.username
            app_logger.info("User: %s", username)

        return "Hello, World!" + str(12222) + username
    except TemplateNotFound:
        abort(404)
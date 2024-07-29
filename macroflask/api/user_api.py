from flask import abort
from flask_jwt_extended import jwt_required
from jinja2 import TemplateNotFound

from tests.util_test.test_query_processor import normal_body, group_by_body
from . import api_bp
from macroflask.models import db
from macroflask.system.user_model import User, PermissionsConstant, RoleModulePermission, \
    ModuleConstant
from ..system.rest_mgmt import permission_required
from ..system.extensions import app_logger
from ..util.query_processor import QueryRequest, QueryProcessor


@api_bp.route('/user/')
@jwt_required()
@permission_required(module_id=ModuleConstant.USER, permission_bitmask=PermissionsConstant.READ)
def show():
    body = normal_body
    gb_body = group_by_body

    try:
        query_request = QueryRequest(gb_body)

        with db.get_db_session() as session:
            # user = session.query(User).where().first()
            # username = user.username
            # app_logger.info("User: %s", username)
            query_processor = QueryProcessor(User, session, None, query_request)
            query = query_processor.process()
            print(query[0].username)

        return "Hello, World!" + str(12222)
    except TemplateNotFound:
        abort(404)
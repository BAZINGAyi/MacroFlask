# check role has permission
import json
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from macroflask import db
from macroflask.system.user_model import RoleModulePermission, User


def permission_required(module_id, permission_bitmask):
    """
    Check if the user has the required permission to access the resource.

    :param module_id:  module id
    :param permission_bitmask: permission bitmask
    :return:
    """
    def decorator(f):
        @wraps(f)  # preserve the original function's metadata
        def decorated_function(*args, **kwargs):
            with db.get_db_session() as session:
                user_id = get_jwt_identity()
                # get user permissions
                permissions = session.query(
                    RoleModulePermission.permissions
                ).select_from(User).join(
                    RoleModulePermission,
                    User.role_id == RoleModulePermission.role_id
                ).filter(
                    User.id == user_id,
                    RoleModulePermission.module_id == module_id
                ).first()

                if not permissions or not RoleModulePermission(
                        permissions=permissions[0]).has_permission(permission_bitmask):
                    return ResponseHandler.error(
                        "You do not have permission to access this resource", status_code=403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


class ResponseHandler:
    @staticmethod
    def success(message, data=None, status_code=200):
        response = {
            "status": "success",
            "message": message,
            "data": data
        }
        return jsonify(response), status_code

    @staticmethod
    def error(message, status_code=400):
        response = {
            "status": "error",
            "message": message
        }
        return jsonify(response), status_code

    @staticmethod
    def convert_error_msg(error):
        error_msg = "Internal Server Error"
        if isinstance(error, ValueError):
            msgs = json.loads(error.json())
            if isinstance(msgs, list):
                for msg in msgs:
                    if 'url' in msg:
                        del msg['url']
            error_msg = msgs
        else:
            error_msg = str(error) if str(error) else error_msg
        return error_msg

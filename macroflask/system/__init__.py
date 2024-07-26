# check role has permission
from functools import wraps

from flask import jsonify, app
from flask_jwt_extended import get_jwt_identity

from macroflask import db
from macroflask.system.extensions import jwt_manager, app_logger
from macroflask.system.user_model import RoleModulePermission, User


def permission_required(module_id, permission_bitmask):
    """
    Check if the user has the required permission to access the resource.

    :param module_id:  module id
    :param permission_bitmask: permission bitmask
    :return:
    """
    def decorator(f):
        @wraps(f)
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


"""
jwt response override
"""


@jwt_manager.invalid_token_loader
def invalid_token_callback(error):
    return ResponseHandler.error("Invalid token", status_code=401)


@jwt_manager.unauthorized_loader
def unauthorized_callback(error):
    return ResponseHandler.error("Missing Authorization Header", status_code=401)


@jwt_manager.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return ResponseHandler.error("Token has expired", status_code=401)


@jwt_manager.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return ResponseHandler.error("Token has been revoked", status_code=401)


@jwt_manager.token_verification_failed_loader
def claims_verification_failed_callback():
    return ResponseHandler.error("Token verification failed", status_code=401)

from flask_jwt_extended import JWTManager

from macroflask.system.rest_mgmt import ResponseHandler

"""
jwt configuration start:
jwt response override:
"""
jwt_manager = JWTManager()


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

"""
jwt configuration end.
"""


def config_jwt():
    pass
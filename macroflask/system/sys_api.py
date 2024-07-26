from datetime import timedelta

from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

from macroflask import db
from macroflask.system import permission_required, ResponseHandler
from macroflask.system.user_model import User, PermissionsConstant

system_api_bp = Blueprint('system', __name__)


@system_api_bp.route("/token", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if not username or not password:
        return ResponseHandler.error("Missing username or password", status_code=400)

    with db.get_db_session() as session:
        user = session.query(User).filter_by(username=username).one_or_none()
        if not user or not user.check_password(password):
            return ResponseHandler.error("Wrong username or password", status_code=401)
        role_id = user.role_id
        user_id = user.id

    # Create a new access token
    token_params = {
        "identity": user_id,
        # "additional_claims": additional_claims,
        "expires_delta": timedelta(days=7)
    }
    access_token = create_access_token(**token_params)
    access_token = "Bearer {}".format(access_token)
    return ResponseHandler.success("Verify success", data={"access_token": access_token})


@system_api_bp.route("/protected", methods=["GET"])
@jwt_required()
@permission_required(module_id=1, permission_bitmask=PermissionsConstant.READ)
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    claims = get_jwt()
    return ResponseHandler.success("Protected route", data={"user_id": current_user, "claims": claims})

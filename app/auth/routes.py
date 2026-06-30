from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, get_jwt, jwt_required

from app.auth.service import AuthenticationError, authenticate, register_user, token_pair
from app.errors import error_response
from app.extensions import db, limiter
from app.tokens.service import revoke_token
from app.users.validation import ValidationError, reject_unknown_fields, require_json_object

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
@limiter.limit("5 per hour")
def register():
    try:
        payload = require_json_object(request.get_json(silent=True))
        reject_unknown_fields(payload, {"name", "email", "password"})
        user = register_user(payload)
    except ValidationError as error:
        return error_response("VALIDATION_ERROR", "Validation failed.", 422, error.details)
    except AuthenticationError as error:
        return error_response(error.code, error.message, error.status)

    return jsonify({"data": user.to_dict(include_private=True)}), 201


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    try:
        payload = require_json_object(request.get_json(silent=True))
        reject_unknown_fields(payload, {"email", "password"})
        user = authenticate(payload.get("email"), payload.get("password"))
    except ValidationError as error:
        return error_response("VALIDATION_ERROR", "Validation failed.", 422, error.details)
    except AuthenticationError as error:
        return error_response(error.code, error.message, error.status)

    return jsonify({"data": {"user": user.to_dict(include_private=True), **token_pair(user)}})


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
@limiter.limit("30 per hour")
def refresh():
    revoke_token(current_user, get_jwt())
    return jsonify({"data": token_pair(current_user, fresh=False)})


@auth_bp.post("/logout")
@jwt_required(verify_type=False)
def logout():
    revoke_token(current_user, get_jwt())
    return jsonify({"message": "Token revoked successfully."})


@auth_bp.post("/logout-all")
@jwt_required(fresh=True)
def logout_all():
    current_user.token_version += 1
    db.session.commit()
    return jsonify({"message": "All tokens were invalidated."})

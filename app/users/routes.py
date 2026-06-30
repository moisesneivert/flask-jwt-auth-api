from __future__ import annotations

import math

from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, jwt_required

from app.errors import error_response
from app.extensions import limiter
from app.users.decorators import roles_required
from app.users.model import UserRole
from app.users.repository import UserRepository
from app.users.service import change_password, update_profile
from app.users.validation import ValidationError, reject_unknown_fields, require_json_object

users_bp = Blueprint("users", __name__)


@users_bp.get("/me")
@jwt_required()
def get_me():
    return jsonify({"data": current_user.to_dict(include_private=True)})


@users_bp.patch("/me")
@jwt_required(fresh=True)
def patch_me():
    payload = require_json_object(request.get_json(silent=True))
    reject_unknown_fields(payload, {"name"})
    try:
        user = update_profile(current_user, payload)
    except ValidationError as error:
        return error_response("VALIDATION_ERROR", "Validation failed.", 422, error.details)
    return jsonify({"data": user.to_dict(include_private=True)})


@users_bp.patch("/me/password")
@jwt_required(fresh=True)
@limiter.limit("5 per hour")
def patch_password():
    payload = require_json_object(request.get_json(silent=True))
    reject_unknown_fields(payload, {"current_password", "new_password"})
    try:
        change_password(
            current_user,
            payload.get("current_password"),
            payload.get("new_password"),
        )
    except ValidationError as error:
        return error_response("VALIDATION_ERROR", "Validation failed.", 422, error.details)
    return jsonify({"message": "Password changed. Existing tokens were invalidated."})


@users_bp.get("")
@jwt_required()
@roles_required(UserRole.ADMIN.value)
def list_users():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)
    search = request.args.get("search", type=str)

    if page < 1 or per_page < 1 or per_page > 100:
        return error_response(
            "INVALID_PAGINATION",
            "page must be at least 1 and per_page must be between 1 and 100.",
            400,
        )

    users, total = UserRepository.list_paginated(page, per_page, search)
    return jsonify(
        {
            "data": [user.to_dict(include_private=True) for user in users],
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": math.ceil(total / per_page) if total else 0,
            },
        }
    )


@users_bp.get("/<string:public_id>")
@jwt_required()
@roles_required(UserRole.ADMIN.value)
def get_user(public_id: str):
    user = UserRepository.get_by_public_id(public_id)
    if user is None:
        return error_response("USER_NOT_FOUND", "User not found.", 404)
    return jsonify({"data": user.to_dict(include_private=True)})


@users_bp.patch("/<string:public_id>/status")
@jwt_required(fresh=True)
@roles_required(UserRole.ADMIN.value)
def update_user_status(public_id: str):
    payload = require_json_object(request.get_json(silent=True))
    reject_unknown_fields(payload, {"is_active"})
    if not isinstance(payload.get("is_active"), bool):
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            422,
            {"is_active": ["is_active must be a boolean."]},
        )

    user = UserRepository.get_by_public_id(public_id)
    if user is None:
        return error_response("USER_NOT_FOUND", "User not found.", 404)
    if user.id == current_user.id and payload["is_active"] is False:
        return error_response("INVALID_OPERATION", "You cannot deactivate yourself.", 409)

    user.is_active = payload["is_active"]
    user.token_version += 1
    UserRepository.save()
    return jsonify({"data": user.to_dict(include_private=True)})

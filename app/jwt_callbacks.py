from __future__ import annotations

from flask_jwt_extended import JWTManager

from app.errors import error_response
from app.tokens.model import RevokedToken
from app.users.model import User


def register_jwt_callbacks(jwt: JWTManager) -> None:
    @jwt.token_in_blocklist_loader
    def token_is_blocked(_jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload.get("jti")
        identity = jwt_payload.get("sub")
        token_version = jwt_payload.get("token_version")

        if jti and RevokedToken.query.filter_by(jti=jti).first() is not None:
            return True

        user = User.query.filter_by(public_id=identity).first()
        return (
            user is None
            or not user.is_active
            or token_version is None
            or token_version != user.token_version
        )

    @jwt.user_lookup_loader
    def load_user(_jwt_header, jwt_payload: dict):
        return User.query.filter_by(public_id=jwt_payload.get("sub")).first()

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return error_response("TOKEN_EXPIRED", "The token has expired.", 401)

    @jwt.invalid_token_loader
    def invalid_token(reason: str):
        return error_response("INVALID_TOKEN", reason, 422)

    @jwt.unauthorized_loader
    def missing_token(reason: str):
        return error_response("AUTHORIZATION_REQUIRED", reason, 401)

    @jwt.revoked_token_loader
    def revoked_token(_jwt_header, _jwt_payload):
        return error_response("TOKEN_REVOKED", "The token is no longer valid.", 401)

    @jwt.needs_fresh_token_loader
    def fresh_token_required(_jwt_header, _jwt_payload):
        return error_response("FRESH_TOKEN_REQUIRED", "A fresh access token is required.", 401)

    @jwt.user_lookup_error_loader
    def user_lookup_failed(_jwt_header, _jwt_payload):
        return error_response("USER_NOT_FOUND", "The token user no longer exists.", 401)

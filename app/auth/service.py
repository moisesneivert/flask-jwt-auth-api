from __future__ import annotations

from datetime import timedelta

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from app.extensions import db
from app.users.model import User, UserRole
from app.users.repository import UserRepository
from app.users.validation import ValidationError, validate_email, validate_name, validate_password
from app.utils import utc_now


class AuthenticationError(ValueError):
    def __init__(self, code: str, message: str, status: int = 401):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def token_pair(user: User, fresh: bool = True) -> dict:
    claims = {"role": user.role, "token_version": user.token_version}
    return {
        "access_token": create_access_token(
            identity=user.public_id, additional_claims=claims, fresh=fresh
        ),
        "refresh_token": create_refresh_token(identity=user.public_id, additional_claims=claims),
        "token_type": "Bearer",
        "access_expires_in": int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()),
        "refresh_expires_in": int(current_app.config["JWT_REFRESH_TOKEN_EXPIRES"].total_seconds()),
    }


def register_user(payload: dict) -> User:
    name = validate_name(payload.get("name"))
    email = validate_email(payload.get("email"))
    password = validate_password(payload.get("password"), email)

    if UserRepository.get_by_email(email):
        raise AuthenticationError("EMAIL_ALREADY_REGISTERED", "Email is already registered.", 409)

    user = User(name=name, email=email, role=UserRole.USER.value)
    user.set_password(password)
    return UserRepository.add(user)


def authenticate(email_value, password_value) -> User:
    try:
        email = validate_email(email_value)
    except ValidationError:
        raise AuthenticationError("INVALID_CREDENTIALS", "Invalid email or password.") from None

    if not isinstance(password_value, str):
        raise AuthenticationError("INVALID_CREDENTIALS", "Invalid email or password.")

    user = UserRepository.get_by_email(email)
    if user is None:
        raise AuthenticationError("INVALID_CREDENTIALS", "Invalid email or password.")
    if not user.is_active:
        raise AuthenticationError("ACCOUNT_DISABLED", "This account is disabled.", 403)
    if user.is_locked():
        raise AuthenticationError(
            "ACCOUNT_TEMPORARILY_LOCKED",
            "Too many failed login attempts. Try again later.",
            423,
        )

    if not user.check_password(password_value):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= current_app.config["MAX_LOGIN_ATTEMPTS"]:
            user.locked_until = utc_now() + timedelta(
                minutes=current_app.config["ACCOUNT_LOCK_MINUTES"]
            )
            user.failed_login_attempts = 0
        db.session.commit()
        raise AuthenticationError("INVALID_CREDENTIALS", "Invalid email or password.")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = utc_now()
    db.session.commit()
    return user

from __future__ import annotations

from app.extensions import db
from app.users.model import User
from app.users.repository import UserRepository
from app.users.validation import ValidationError, validate_name, validate_password


def update_profile(user: User, payload: dict) -> User:
    if "name" not in payload:
        raise ValidationError({"name": ["Name is required."]})
    user.name = validate_name(payload["name"])
    UserRepository.save()
    return user


def change_password(user: User, current_password, new_password) -> None:
    if not isinstance(current_password, str) or not user.check_password(current_password):
        raise ValidationError({"current_password": ["The current password is incorrect."]})

    validated = validate_password(new_password, user.email)
    if user.check_password(validated):
        raise ValidationError({"new_password": ["The new password must be different."]})

    user.set_password(validated)
    user.token_version += 1
    db.session.commit()

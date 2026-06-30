from __future__ import annotations

from functools import wraps

from flask_jwt_extended import current_user

from app.errors import error_response


def roles_required(*allowed_roles: str):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user is None or current_user.role not in allowed_roles:
                return error_response(
                    "INSUFFICIENT_PERMISSIONS",
                    "You do not have permission to access this resource.",
                    403,
                )
            return function(*args, **kwargs)

        return wrapper

    return decorator

from __future__ import annotations

import re

EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


class ValidationError(ValueError):
    def __init__(self, details: dict[str, list[str]]):
        super().__init__("Validation failed")
        self.details = details


def require_json_object(payload) -> dict:
    if not isinstance(payload, dict):
        raise ValidationError({"body": ["A JSON object is required."]})
    return payload


def validate_email(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError({"email": ["Email is required."]})
    normalized = value.strip().lower()
    if len(normalized) > 255 or not EMAIL_PATTERN.fullmatch(normalized):
        raise ValidationError({"email": ["Enter a valid email address."]})
    return normalized


def validate_name(value) -> str:
    if not isinstance(value, str):
        raise ValidationError({"name": ["Name must be a string."]})
    normalized = " ".join(value.split())
    if len(normalized) < 2 or len(normalized) > 120:
        raise ValidationError({"name": ["Name must contain between 2 and 120 characters."]})
    return normalized


def validate_password(value, email: str | None = None) -> str:
    errors = []
    if not isinstance(value, str):
        raise ValidationError({"password": ["Password must be a string."]})
    if len(value) < 10:
        errors.append("Password must contain at least 10 characters.")
    if len(value) > 128:
        errors.append("Password must contain at most 128 characters.")
    if not re.search(r"[a-z]", value):
        errors.append("Password must contain a lowercase letter.")
    if not re.search(r"[A-Z]", value):
        errors.append("Password must contain an uppercase letter.")
    if not re.search(r"\d", value):
        errors.append("Password must contain a number.")
    if not re.search(r"[^A-Za-z0-9]", value):
        errors.append("Password must contain a special character.")
    if email:
        local_part = email.split("@", maxsplit=1)[0]
        if len(local_part) >= 4 and local_part.lower() in value.lower():
            errors.append("Password must not contain the email username.")
    if errors:
        raise ValidationError({"password": errors})
    return value


def reject_unknown_fields(payload: dict, allowed_fields: set[str]) -> None:
    unknown = sorted(set(payload) - allowed_fields)
    if unknown:
        raise ValidationError({"body": [f"Unknown fields: {', '.join(unknown)}."]})

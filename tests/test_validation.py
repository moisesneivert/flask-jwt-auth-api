import pytest

from app.users.validation import (
    ValidationError,
    reject_unknown_fields,
    require_json_object,
    validate_email,
    validate_name,
    validate_password,
)
from app.utils import ensure_utc


def test_require_json_object_rejects_non_object():
    with pytest.raises(ValidationError):
        require_json_object(None)


def test_email_validation_paths():
    with pytest.raises(ValidationError):
        validate_email(123)
    with pytest.raises(ValidationError):
        validate_email("invalid")
    assert validate_email("  USER@Example.COM ") == "user@example.com"


def test_name_validation_paths():
    with pytest.raises(ValidationError):
        validate_name(None)
    with pytest.raises(ValidationError):
        validate_name("x")
    assert validate_name("  Maria   Silva ") == "Maria Silva"


def test_password_validation_paths():
    with pytest.raises(ValidationError):
        validate_password(None)
    with pytest.raises(ValidationError) as weak:
        validate_password("a" * 129)
    assert "Password must contain at most 128 characters." in weak.value.details["password"]
    with pytest.raises(ValidationError) as contains_email:
        validate_password("UserNamePass1!", "username@example.com")
    assert (
        "Password must not contain the email username." in contains_email.value.details["password"]
    )
    assert validate_password("ValidPass1!") == "ValidPass1!"


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        reject_unknown_fields({"name": "A", "admin": True}, {"name"})
    reject_unknown_fields({"name": "A"}, {"name"})


def test_ensure_utc_accepts_none():
    assert ensure_utc(None) is None

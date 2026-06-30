import pytest
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.config import ProductionConfig, _database_url
from app.users.validation import ValidationError


def test_database_url_normalization(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")
    assert _database_url().startswith("postgresql+psycopg://")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    assert _database_url().startswith("postgresql+psycopg://")


def test_production_config_rejects_weak_secrets(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "development-only-secret")
    monkeypatch.setattr(ProductionConfig, "JWT_SECRET_KEY", "strong-enough")
    with pytest.raises(RuntimeError):
        ProductionConfig.validate()


def test_http_and_unexpected_error_handlers(app):
    @app.get("/test-error")
    def test_error():
        raise RuntimeError("boom")

    client = app.test_client()
    not_found = client.get("/missing")
    assert not_found.status_code == 404
    assert not_found.get_json()["error"]["code"] == "NOT_FOUND"
    unexpected = client.get("/test-error")
    assert unexpected.status_code == 500
    assert unexpected.get_json()["error"]["code"] == "INTERNAL_SERVER_ERROR"


def test_database_error_handler(app):
    @app.get("/test-database-error")
    def test_database_error():
        raise SQLAlchemyError("database failed")

    response = app.test_client().get("/test-database-error")
    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == "DATABASE_ERROR"


def test_unknown_configuration_is_rejected():
    with pytest.raises(ValueError):
        create_app("invalid")


def test_global_validation_error_handler(app):
    @app.get("/test-validation-error")
    def test_validation_error():
        raise ValidationError({"field": ["invalid"]})

    response = app.test_client().get("/test-validation-error")
    assert response.status_code == 422
    assert response.get_json()["error"]["details"] == {"field": ["invalid"]}

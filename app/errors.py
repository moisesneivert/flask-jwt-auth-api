from __future__ import annotations

from flask import Flask, jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.extensions import db


def error_response(code: str, message: str, status: int, details=None):
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return jsonify(payload), status


def register_error_handlers(app: Flask) -> None:
    from app.users.validation import ValidationError

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return error_response("VALIDATION_ERROR", "Validation failed.", 422, error.details)

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return error_response(
            code=error.name.upper().replace(" ", "_"),
            message=error.description,
            status=error.code or 500,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error: SQLAlchemyError):
        db.session.rollback()
        app.logger.exception("Database error")
        return error_response("DATABASE_ERROR", "A database operation failed.", 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        db.session.rollback()
        app.logger.exception("Unexpected error")
        return error_response("INTERNAL_SERVER_ERROR", "An unexpected error occurred.", 500)

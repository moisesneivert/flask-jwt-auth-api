from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from app.commands import register_commands
from app.config import config_by_name
from app.errors import register_error_handlers
from app.extensions import db, jwt, limiter, migrate
from app.jwt_callbacks import register_jwt_callbacks


def create_app(config_name: str | None = None) -> Flask:
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    selected_config = config_name or os.getenv("FLASK_ENV", "development")
    if selected_config not in config_by_name:
        raise ValueError(f"Unknown configuration: {selected_config}")
    config_class = config_by_name[selected_config]
    if selected_config == "production":
        config_class.validate()
    app.config.from_object(config_class)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    register_blueprints(app)
    register_error_handlers(app)
    register_jwt_callbacks(jwt)
    register_commands(app)
    register_security_headers(app)
    configure_logging(app)

    return app


def register_blueprints(app: Flask) -> None:
    from app.auth.routes import auth_bp
    from app.health.routes import health_bp
    from app.users.routes import users_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")


def register_security_headers(app: Flask) -> None:
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response


def configure_logging(app: Flask) -> None:
    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    app.logger.setLevel(level)

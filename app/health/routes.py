from pathlib import Path

from flask import Blueprint, jsonify, send_from_directory
from sqlalchemy import text

from app.extensions import db, limiter

health_bp = Blueprint("health", __name__)


@health_bp.get("/")
@limiter.exempt
def index():
    return jsonify(
        {
            "name": "Flask JWT Authentication API",
            "version": "1.0.0",
            "documentation": "/docs/openapi.yaml",
        }
    )


@health_bp.get("/health")
@limiter.exempt
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify({"status": "healthy", "database": "reachable"})


@health_bp.get("/docs/openapi.yaml")
@limiter.exempt
def openapi_document():
    docs_directory = Path(__file__).resolve().parents[2] / "docs"
    return send_from_directory(docs_directory, "openapi.yaml", mimetype="application/yaml")

from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db
from app.users.model import User, UserRole


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def user(app):
    with app.app_context():
        item = User(name="Regular User", email="user@example.com", role=UserRole.USER.value)
        item.set_password("StrongPass1!")
        db.session.add(item)
        db.session.commit()
        return item.public_id


@pytest.fixture()
def admin(app):
    with app.app_context():
        item = User(name="Admin User", email="admin@example.com", role=UserRole.ADMIN.value)
        item.set_password("AdminPass1!")
        db.session.add(item)
        db.session.commit()
        return item.public_id


def login(client, email="user@example.com", password="StrongPass1!"):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.get_json()["data"]


@pytest.fixture()
def user_tokens(client, user):
    return login(client)


@pytest.fixture()
def admin_tokens(client, admin):
    return login(client, "admin@example.com", "AdminPass1!")


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

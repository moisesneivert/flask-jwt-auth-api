from tests.conftest import bearer


def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "New User", "email": "NEW@example.com", "password": "SecurePass1!"},
    )
    assert response.status_code == 201
    body = response.get_json()["data"]
    assert body["email"] == "new@example.com"
    assert "password_hash" not in body


def test_register_rejects_weak_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "New User", "email": "new@example.com", "password": "weak"},
    )
    assert response.status_code == 422
    assert "password" in response.get_json()["error"]["details"]


def test_register_duplicate_email(client, user):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Another", "email": "USER@example.com", "password": "SecurePass1!"},
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_login_returns_access_and_refresh_tokens(client, user):
    response = client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "StrongPass1!"}
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["user"]["email"] == "user@example.com"


def test_login_rejects_invalid_credentials(client, user):
    response = client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "WrongPass1!"}
    )
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_account_is_locked_after_repeated_failures(client, user):
    for _ in range(3):
        client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "WrongPass1!"},
        )
    response = client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "StrongPass1!"}
    )
    assert response.status_code == 423


def test_refresh_creates_non_fresh_access_token(client, user_tokens):
    response = client.post("/api/v1/auth/refresh", headers=bearer(user_tokens["refresh_token"]))
    assert response.status_code == 200
    assert response.get_json()["data"]["access_token"]


def test_logout_revokes_current_token(client, user_tokens):
    headers = bearer(user_tokens["access_token"])
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    blocked = client.get("/api/v1/users/me", headers=headers)
    assert blocked.status_code == 401
    assert blocked.get_json()["error"]["code"] == "TOKEN_REVOKED"


def test_logout_all_invalidates_access_and_refresh(client, user_tokens):
    response = client.post("/api/v1/auth/logout-all", headers=bearer(user_tokens["access_token"]))
    assert response.status_code == 200
    assert (
        client.get("/api/v1/users/me", headers=bearer(user_tokens["access_token"])).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/refresh", headers=bearer(user_tokens["refresh_token"])
        ).status_code
        == 401
    )


def test_register_rejects_non_json_and_unknown_fields(client):
    assert client.post("/api/v1/auth/register").status_code == 422
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "New User",
            "email": "new@example.com",
            "password": "SecurePass1!",
            "is_admin": True,
        },
    )
    assert response.status_code == 422


def test_login_handles_invalid_input_unknown_and_disabled_users(client, app, user):
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "invalid", "password": "Anything1!"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "missing@example.com", "password": "Anything1!"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "user@example.com", "password": 123}
        ).status_code
        == 401
    )

    from app.extensions import db
    from app.users.model import User

    with app.app_context():
        item = User.query.filter_by(public_id=user).first()
        item.is_active = False
        db.session.commit()
    response = client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "StrongPass1!"}
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "ACCOUNT_DISABLED"

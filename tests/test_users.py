from tests.conftest import bearer, login


def test_protected_route_requires_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_get_current_user(client, user_tokens):
    response = client.get("/api/v1/users/me", headers=bearer(user_tokens["access_token"]))
    assert response.status_code == 200
    assert response.get_json()["data"]["email"] == "user@example.com"


def test_update_profile_requires_fresh_token(client, user_tokens):
    refreshed = client.post(
        "/api/v1/auth/refresh", headers=bearer(user_tokens["refresh_token"])
    ).get_json()["data"]["access_token"]
    response = client.patch("/api/v1/users/me", json={"name": "Updated"}, headers=bearer(refreshed))
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "FRESH_TOKEN_REQUIRED"


def test_update_profile(client, user_tokens):
    response = client.patch(
        "/api/v1/users/me",
        json={"name": "Updated User"},
        headers=bearer(user_tokens["access_token"]),
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["name"] == "Updated User"


def test_change_password_invalidates_existing_tokens(client, user_tokens):
    response = client.patch(
        "/api/v1/users/me/password",
        json={"current_password": "StrongPass1!", "new_password": "DifferentPass2@"},
        headers=bearer(user_tokens["access_token"]),
    )
    assert response.status_code == 200
    assert (
        client.get("/api/v1/users/me", headers=bearer(user_tokens["access_token"])).status_code
        == 401
    )
    assert login(client, "user@example.com", "DifferentPass2@")["access_token"]


def test_regular_user_cannot_list_users(client, user_tokens):
    response = client.get("/api/v1/users", headers=bearer(user_tokens["access_token"]))
    assert response.status_code == 403


def test_admin_can_list_and_get_users(client, user, admin_tokens):
    headers = bearer(admin_tokens["access_token"])
    response = client.get("/api/v1/users?per_page=1", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["meta"]["total"] == 2

    response = client.get(f"/api/v1/users/{user}", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["data"]["email"] == "user@example.com"


def test_admin_can_deactivate_user_and_tokens_stop_working(client, user, user_tokens, admin_tokens):
    response = client.patch(
        f"/api/v1/users/{user}/status",
        json={"is_active": False},
        headers=bearer(admin_tokens["access_token"]),
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["is_active"] is False
    assert (
        client.get("/api/v1/users/me", headers=bearer(user_tokens["access_token"])).status_code
        == 401
    )


def test_profile_and_password_validation_errors(client, user_tokens):
    headers = bearer(user_tokens["access_token"])
    assert client.patch("/api/v1/users/me", json={}, headers=headers).status_code == 422
    assert (
        client.patch(
            "/api/v1/users/me/password",
            json={"current_password": "wrong", "new_password": "DifferentPass2@"},
            headers=headers,
        ).status_code
        == 422
    )
    assert (
        client.patch(
            "/api/v1/users/me/password",
            json={"current_password": "StrongPass1!", "new_password": "StrongPass1!"},
            headers=headers,
        ).status_code
        == 422
    )


def test_admin_user_edge_cases(client, admin, admin_tokens):
    headers = bearer(admin_tokens["access_token"])
    assert client.get("/api/v1/users?page=0", headers=headers).status_code == 400
    assert client.get("/api/v1/users?search=admin", headers=headers).status_code == 200
    assert client.get("/api/v1/users/does-not-exist", headers=headers).status_code == 404
    assert (
        client.patch(
            "/api/v1/users/does-not-exist/status", json={"is_active": True}, headers=headers
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v1/users/{admin}/status", json={"is_active": "no"}, headers=headers
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/v1/users/{admin}/status", json={"is_active": False}, headers=headers
        ).status_code
        == 409
    )

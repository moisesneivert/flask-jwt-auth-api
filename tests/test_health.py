def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Flask JWT Authentication API"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy", "database": "reachable"}


def test_openapi_document(client):
    response = client.get("/docs/openapi.yaml")
    assert response.status_code == 200
    assert b"openapi: 3.1.0" in response.data

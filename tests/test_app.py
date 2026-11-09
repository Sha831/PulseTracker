def test_app_starts(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

def test_redis_connection(client):
    redis_client = client.app.state.redis_client

    assert redis_client.ping() is True
import pytest
from starlette.testclient import TestClient

from engage_api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_base_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

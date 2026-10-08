"""Shared pytest fixtures."""
import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    """A fresh app with its own temporary database for every test."""
    test_app = create_app(db_path=str(tmp_path / "test.db"))
    test_app.config["TESTING"] = True
    return test_app


@pytest.fixture
def client(app):
    """Flask test client: lets us call endpoints without a real server."""
    return app.test_client()


@pytest.fixture
def sample_client(client):
    """Creates one client called 'Arjun' that tests can use."""
    client.post("/clients", json={
        "name": "Arjun", "age": 28, "height": 175,
        "weight": 70, "program": "MG",
    })
    return "Arjun"

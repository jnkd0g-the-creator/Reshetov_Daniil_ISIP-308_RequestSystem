"""Fresh SQLite for every test; no dependency on the user's running app."""

import secrets
from contextlib import ExitStack

import pytest
from fastapi.testclient import TestClient

from coffeedesk.app import create_app
from coffeedesk.config import Settings
from coffeedesk.database import Database
from coffeedesk.repository import Repository
from coffeedesk.security import password_hash
from coffeedesk.services import RequestService


@pytest.fixture(scope="session")
def demo_password():
    return secrets.token_urlsafe(24)


@pytest.fixture(scope="session")
def demo_hash(demo_password):
    return password_hash(demo_password)


@pytest.fixture
def database(tmp_path, demo_hash):
    database = Database(tmp_path / "isolated.db")
    database.initialize(demo=True)
    with database.transaction(write=True) as con:
        repo = Repository(con)
        for user in repo.users():
            repo.set_password(user["id"], demo_hash)
    return database


@pytest.fixture
def service(database):
    return RequestService(database)


@pytest.fixture
def users(database):
    with database.transaction() as con:
        repo = Repository(con)
        return {name: repo.user(identifier) for name, identifier in [("admin", 1), ("operator", 2), ("tech1", 3), ("tech2", 4), ("barista1", 5), ("barista2", 6)]}


@pytest.fixture
def payload():
    return {"title": "Протекает тестовый кран", "description": "Необходимо заменить уплотнение у основания крана рабочей мойки.", "cafe_id": 1, "category_id": 1, "priority": "high"}


@pytest.fixture
def app(database):
    return create_app(Settings(db_path=database.path, mode="test"))


@pytest.fixture
def clients(app, demo_password):
    with ExitStack() as stack:
        def make(username="admin"):
            client = stack.enter_context(TestClient(app))
            response = client.post("/auth/login", json={"username": username, "password": demo_password})
            assert response.status_code == 200
            client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
            return client
        yield make

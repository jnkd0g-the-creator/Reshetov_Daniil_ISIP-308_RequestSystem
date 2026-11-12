import secrets

from coffeedesk.database import Database
from coffeedesk.models import RequestCreate
from coffeedesk.repository import Repository
from coffeedesk.services import RequestService


def test_service_lifecycle_and_persistence(tmp_path):
    db = Database(tmp_path / "smoke.db")
    db.initialize(demo=True)
    service = RequestService(db)
    with db.transaction() as con:
        admin = Repository(con).user(1)
        barista = Repository(con).user(5)
    item = service.create(barista, RequestCreate(title="Протекает учебный кран", description="Проверка реального сохранения обращения в SQLite.", cafe_id=1, category_id=1))
    service.update(barista, item["id"], {"priority": "high"})
    service.assign(admin, item["id"], 3)
    for status in ("in_progress", "done", "closed"):
        service.change_status(admin, item["id"], status)
    service.add_comment(admin, item["id"], {"body": "Результат ремонта проверен."})
    service.archive(admin, item["id"], confirmed=True)
    assert RequestService(Database(db.path)).get(admin, item["id"])["archived"] is True
    assert len(service.history(admin, item["id"])) == 7
    assert service.comments(admin, item["id"])[0]["body"] == "Результат ремонта проверен."


def test_web_login_and_creation(tmp_path):
    from fastapi.testclient import TestClient

    from coffeedesk.app import create_app
    from coffeedesk.config import Settings
    from coffeedesk.security import password_hash

    settings = Settings(db_path=tmp_path / "web.db", mode="test")
    db = Database(settings.db_path)
    db.initialize(demo=True)
    password = secrets.token_urlsafe(20)
    with db.transaction(write=True) as con:
        Repository(con).set_password(5, password_hash(password))
    with TestClient(create_app(settings)) as client:
        assert client.get("/").status_code == 200
        assert client.get("/health").json()["database"] == "ok"
        response = client.post("/ui-api/auth/login", json={"username": "barista1", "password": password})
        assert response.status_code == 200
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        response = client.post("/ui-api/requests", json={"title": "Проверка формы", "description": "Заявка записывается контроллером в реальную тестовую SQLite.", "cafe_id": 1, "category_id": 1})
        assert response.status_code == 201
        assert client.get(f"/ui-api/requests/{response.json()['id']}").json()["title"] == "Проверка формы"

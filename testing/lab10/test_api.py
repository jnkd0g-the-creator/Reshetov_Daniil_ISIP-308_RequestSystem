import pytest
from fastapi.testclient import TestClient


def test_api_create_success_and_location(clients, payload):
    client = clients("barista1")
    response = client.post("/requests",json=payload)
    assert response.status_code == 201
    assert response.headers["Location"] == f"/requests/{response.json()['id']}"
    assert client.get(response.headers["Location"]).json()["title"] == payload["title"]


def test_api_bad_input_422(clients):
    response = clients().post("/requests",json={"title":""})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert all(set(detail)=={"field","type"} for detail in response.json()["error"]["details"])


def test_api_missing_and_invalid_id(clients):
    client = clients()
    assert client.get("/requests/99999999").status_code == 404
    assert client.get("/requests/-1").status_code == 422
    assert client.get("/requests/not-an-id").status_code == 422


@pytest.mark.parametrize("field", ["cafe_id","category_id"])
@pytest.mark.parametrize("value", [True,False,"1",0,-1])
def test_regression_bug01_strict_integer_ids(clients, database, payload, field, value):
    response = clients().post("/requests",json=dict(payload,**{field:value}))
    # Before BUG-01 fix, True was accepted and this assert genuinely failed.
    assert response.status_code == 422
    with database.transaction() as con:
        assert con.execute("SELECT COUNT(*) FROM Requests").fetchone()[0] == 12


@pytest.mark.parametrize("body", [{},{"title":None},{"status_code":"closed"}])
def test_patch_empty_null_extra_are_rejected(clients, body):
    assert clients().patch("/requests/1",json=body).status_code == 422


def test_regression_role_scope_and_direct_http(clients, payload):
    applicant = clients("barista1")
    assert applicant.get("/requests/2").status_code == 404
    assert all(item["applicant_id"]==5 for item in applicant.get("/requests").json())
    assert clients("tech1").post("/requests",json=payload).status_code == 403


def test_csrf_enforced_even_with_cookie(clients, payload):
    client = clients()
    del client.headers["X-CSRF-Token"]
    response = client.post("/requests",json=payload)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


def test_unauthenticated_requests_401(app):
    with TestClient(app) as client:
        assert client.get("/requests").status_code == 401


def test_patch_data_persist(clients):
    client = clients()
    assert client.patch("/requests/1",json={"priority":"urgent"}).status_code == 200
    assert client.get("/requests/1").json()["priority"] == "urgent"


def test_delete_is_archive_not_physical_delete(clients, database):
    client = clients()
    assert client.delete("/requests/12").status_code == 400
    response = client.delete("/requests/12?confirm=true")
    assert response.status_code == 204 and response.content == b""
    with database.transaction() as con:
        assert con.execute("SELECT archived FROM Requests WHERE id=12").fetchone()[0] == 1
        assert con.execute("SELECT COUNT(*) FROM Comments WHERE request_id=12").fetchone()[0] == 1


def test_users_response_excludes_secrets(clients):
    users = clients().get("/users").json()
    assert len(users)==6
    assert all(set(user)=={"id","username","name","role_code","active"} for user in users)
    assert len(clients("barista1").get("/users").json())==1


def test_api_catalogs_and_history(clients):
    client = clients()
    assert len(client.get("/statuses").json())==4
    assert len(client.get("/categories").json())==5
    assert len(client.get("/cafes").json())==3
    assert client.get("/requests/1/history").json()[0]["event"]=="seeded"
    assert client.get("/requests/1/comments").status_code==200


def test_openapi_and_static_frontend(app):
    with TestClient(app) as client:
        schema=client.get("/openapi.json").json()
        assert "/requests" in schema["paths"]
        assert "/ui-api/requests" not in schema["paths"]
        assert "APIKeyCookie" in schema["components"]["securitySchemes"]
        assert client.get("/").status_code==200
        assert client.get("/assets/app.js").status_code==200
        assert client.get("/docs").status_code==200


def test_health_checks_actual_database(app, tmp_path):
    with TestClient(app) as client:
        assert client.get("/health").json()["database"]=="ok"
        directory=tmp_path / "not-a-database"
        directory.mkdir()
        app.state.database.path=directory
        response=client.get("/health")
        assert response.status_code==503
        assert response.json()["error"]["code"]=="database_unavailable"

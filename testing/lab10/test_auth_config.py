import time

import pytest
from fastapi.testclient import TestClient

from coffeedesk.config import Settings
from coffeedesk.errors import DomainError
from coffeedesk.security import token_hash, verify_password


def test_password_hash_and_wrong_password(demo_password, demo_hash):
    assert demo_hash.startswith("pbkdf2_sha256$600000$")
    assert verify_password(demo_password,demo_hash)
    assert not verify_password("incorrect",demo_hash)
    assert not verify_password("incorrect","!unset")


def test_session_expiration(app, database, demo_password):
    user, token, csrf=app.state.auth.login("admin",demo_password)
    assert user["role_code"]=="admin"
    with database.transaction(write=True) as con:
        con.execute("UPDATE Sessions SET expires_at=? WHERE token_hash=?",(int(time.time())-1,token_hash(token)))
    with pytest.raises(DomainError) as error:
        app.state.auth.authenticate(token,csrf,True)
    assert error.value.status==401


def test_logout_invalidates_session(clients):
    client=clients()
    assert client.post("/auth/logout").status_code==204
    assert client.get("/auth/me").status_code==401


def test_wrong_password_error_is_generic_and_no_echo(app):
    with TestClient(app) as client:
        response=client.post("/auth/login",json={"username":"unknown_user","password":"private-example-never-echo"})
        assert response.status_code==401
        assert "private-example-never-echo" not in response.text
        assert response.json()["error"]["message"]=="Неверный логин или пароль."


def test_explicit_password_too_long_not_reflected(app):
    secret="secret-value"*30
    with TestClient(app) as client:
        response=client.post("/auth/login",json={"username":"admin","password":secret})
        assert response.status_code==422 and secret not in response.text


def test_cookie_attributes(clients):
    client=clients()
    cookies=client.cookies.jar
    cookie=next(c for c in cookies if c.name=="coffee_session")
    assert cookie.has_nonstandard_attr("HttpOnly")
    assert cookie.get_nonstandard_attr("SameSite")=="lax"
    assert cookie.expires is not None


def test_production_disallows_insecure_cookie(monkeypatch):
    monkeypatch.setenv("COFFEE_MODE","production")
    monkeypatch.setenv("COFFEE_SECURE_COOKIES","false")
    with pytest.raises(ValueError,match="Secure"):
        Settings.from_env()


@pytest.mark.parametrize("port", ["0","65536"])
def test_invalid_port(monkeypatch, port):
    monkeypatch.setenv("COFFEE_MODE","development")
    monkeypatch.setenv("PORT",port)
    with pytest.raises(ValueError,match="PORT"):
        Settings.from_env()

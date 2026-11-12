"""Actual Docker build, non-root init, HTTP and named-volume persistence proof."""

import json
import os
import subprocess
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/deployment"


def main():
    env = dict(os.environ, PORT="8001", COFFEE_BIND="127.0.0.1", COFFEE_MODE="development", COFFEE_SECURE_COOKIES="false")
    log = []
    prefix = ["docker", "compose", "-p", "coffeedesk-labs"]

    def command(args, retain=True):
        result = subprocess.run(args, cwd=ROOT, env=env, text=True, capture_output=True)
        if retain:
            log.append("$ " + " ".join(args) + "\n" + result.stdout + result.stderr)
        assert result.returncode == 0, result.stderr
        return result.stdout

    command(["docker", "version", "--format", "Client={{.Client.Version}} Server={{.Server.Version}}"])
    command([*prefix, "--progress", "plain", "build"])
    command([*prefix, "run", "--rm", "coffee", "python", "-m", "coffeedesk", "init-db", "--demo", "--credentials", "/app/data/demo_credentials.txt"])
    command([*prefix, "up", "-d", "--wait", "--wait-timeout", "90"])
    container = command([*prefix, "ps", "-q", "coffee"]).strip()
    info = command(["docker", "inspect", "--format", "ID={{.Id}} User={{.Config.User}} Health={{.State.Health.Status}}", container])
    assert "User=10001:10001" in info and "Health=healthy" in info
    command([*prefix, "exec", "-T", "coffee", "id"])
    command([*prefix, "exec", "-T", "coffee", "python", "--version"])
    # Secret output is captured in memory, never retained in public logs.
    raw = command([*prefix, "exec", "-T", "coffee", "cat", "/app/data/demo_credentials.txt"], retain=False)
    credentials = dict(line.split("\t") for line in raw.splitlines())
    private = ROOT / ".local/docker_credentials.txt"
    private.parent.mkdir(exist_ok=True)
    fd = os.open(private, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(raw)
    with httpx.Client(base_url="http://127.0.0.1:8001") as client:
        response = client.get("/health")
        assert response.status_code == 200
        log.append("GET /health → 200 " + json.dumps(response.json()))
        auth = client.post("/auth/login", json={"username": "admin", "password": credentials["admin"]})
        assert auth.status_code == 200
        client.headers["X-CSRF-Token"] = auth.json()["csrf_token"]
        log.append("POST /auth/login → 200 (credentials/session/CSRF omitted)")
        assert len(client.get("/requests").json()) >= 12
        response = client.post("/requests", json={"title": "Контейнерная проверка крана", "description": "Эта заявка должна сохраниться после пересоздания Docker-контейнера.", "cafe_id": 1, "category_id": 1})
        assert response.status_code == 201
        item = response.json()
        log.append(f"POST /requests → 201; id={item['id']}")
        command([*prefix, "up", "-d", "--force-recreate", "--wait", "--wait-timeout", "90"])
        new_container = command([*prefix, "ps", "-q", "coffee"]).strip()
        assert new_container != container
        response = client.get(f"/requests/{item['id']}")
        assert response.status_code == 200 and response.json()["title"] == item["title"]
        log.append(f"New container ID differs: PASS. GET /requests/{item['id']} → 200, title persisted: PASS. Session also persisted in SQLite.")
        client.post("/auth/logout")
    command([*prefix, "ps"])
    command(["docker", "image", "inspect", "coffeedesk:local", "--format", "Image={{.Id}} Size={{.Size}} User={{.Config.User}}"])
    log.append("REMOTE DEPLOYMENT: BLOCKED — no agreed SSH server or external URL provided. This run proves only local container deployment on the current machine (127.0.0.1:8001). No public port was opened.")
    (OUTPUT / "docker_run.txt").write_text("\n\n".join(log), encoding="utf-8")
    print("Docker: build/init/healthy/non-root/HTTP/persistence PASS; remote deployment BLOCKED")


if __name__ == "__main__":
    main()

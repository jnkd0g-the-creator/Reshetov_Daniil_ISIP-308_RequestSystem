"""Verify README install and actual HTTP launch in a new venv + fresh SQLite."""

import http.cookiejar
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    logs = []
    with tempfile.TemporaryDirectory(prefix="coffee-clean-", dir="/tmp/opencode") as tmp:
        tmp = Path(tmp)
        env = dict(os.environ, COFFEE_DB_PATH=str(tmp / "fresh.db"), COFFEE_MODE="development", COFFEE_SECURE_COOKIES="false")
        subprocess.run([sys.executable, "-m", "venv", str(tmp / "venv")], check=True)
        python = str(tmp / "venv/bin/python")
        for args in [[python, "-m", "pip", "install", "-r", "requirements.txt"], [python, "-m", "pip", "install", "-e", ".", "--no-deps"], [python, "-m", "coffeedesk", "init-db", "--demo", "--credentials", str(tmp / "credentials.txt")]]:
            result = subprocess.run(args, cwd=ROOT, env=env, text=True, capture_output=True)
            logs.append("$ " + " ".join(args) + "\n" + result.stdout + result.stderr)
            assert result.returncode == 0, logs[-1]
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            env["PORT"] = str(sock.getsockname()[1])
        with (tmp / "server-output").open("w+") as stream:
            server = subprocess.Popen([python, "-m", "coffeedesk", "serve"], cwd=ROOT, env=env, stdout=stream, stderr=stream)
            try:
                base = "http://127.0.0.1:" + env["PORT"]
                for _ in range(100):
                    try:
                        with urllib.request.urlopen(base + "/health", timeout=1) as response:
                            assert json.load(response)["database"] == "ok"
                        break
                    except urllib.error.URLError:
                        if server.poll() is not None:
                            raise AssertionError("Clean server exited")
                        time.sleep(.1)
                else:
                    raise AssertionError("Clean server failed to become ready")
                jar = http.cookiejar.CookieJar()
                client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
                credentials = dict(line.split("\t") for line in (tmp / "credentials.txt").read_text().splitlines())
                payload = json.dumps({"username": "admin", "password": credentials["admin"]}).encode()
                with client.open(urllib.request.Request(base + "/auth/login", data=payload, headers={"Content-Type": "application/json"})) as response:
                    auth = json.load(response)
                with client.open(base + "/requests") as response:
                    assert len(json.load(response)) == 12
                payload = json.dumps({"title": "Чистый запуск", "description": "Проверка установки по README в новом окружении.", "cafe_id": 1, "category_id": 1}).encode()
                with client.open(urllib.request.Request(base + "/requests", data=payload, headers={"Content-Type": "application/json", "X-CSRF-Token": auth["csrf_token"]})) as response:
                    assert response.status == 201
                logs.append("PASS: brand-new Python venv, requirements install, editable install, fresh demo database, HTTP health, login, 12 requests, POST 201. No credentials retained. Temporary data removed by TemporaryDirectory.")
            finally:
                server.terminate()
                server.wait(timeout=15)
                stream.seek(0)
                logs.append(stream.read())
    output = ROOT / "docs/deployment/clean_start.txt"
    output.write_text("\n\n".join(logs), encoding="utf-8")
    print("Clean installation and real HTTP startup: PASS")


if __name__ == "__main__":
    main()

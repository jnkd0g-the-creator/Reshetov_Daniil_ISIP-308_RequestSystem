"""Isolated HTTP/SQLite fixture shared by evidence and demo recording scripts."""

import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import httpx

from coffeedesk.__main__ import initialize_demo
from coffeedesk.config import Settings

ROOT = Path(__file__).resolve().parents[1]


def source_hash():
    digest = hashlib.sha256()
    for path in sorted((ROOT / "src/coffeedesk").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            digest.update(str(path.relative_to(ROOT)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


@contextmanager
def isolated_server(output):
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="coffee-tests-", dir="/tmp/opencode") as tmp:
        tmp = Path(tmp)
        settings = Settings(db_path=tmp / "test.db", mode="test")
        credentials_path = tmp / "credentials.txt"
        initialize_demo(settings, credentials_path)
        credentials = dict(line.split("\t") for line in credentials_path.read_text().splitlines())
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ, COFFEE_DB_PATH=str(settings.db_path), COFFEE_MODE="test", COFFEE_SECURE_COOKIES="false", PORT=str(port))
        base = f"http://127.0.0.1:{port}"
        with (output / "server.txt").open("w+") as log:
            server = subprocess.Popen([sys.executable, "-m", "coffeedesk", "serve"], cwd=ROOT, env=env, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    try:
                        if httpx.get(base + "/health").status_code == 200:
                            break
                    except httpx.ConnectError:
                        if server.poll() is not None:
                            raise RuntimeError("Isolated server exited")
                    time.sleep(.1)
                else:
                    raise RuntimeError("Isolated server startup timed out")
                metadata = {"date": "2026-11-12", "version": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "source_sha256": source_hash(), "source_uncommitted": subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "src"], cwd=ROOT).returncode != 0, "address": base, "python": sys.version, "os": "Ubuntu 26.04", "browser": "Chromium 140 / Playwright 1.55.0", "data": "temporary SQLite, 12 seeded requests, 6 users; removed after run"}
                (output / "environment.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
                yield base, settings, credentials, credentials_path
            finally:
                server.terminate()
                server.wait(timeout=15)

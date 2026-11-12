"""Record the original boolean-ID defect before changing application code."""

import json
import secrets
import subprocess
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from coffeedesk.app import create_app
from coffeedesk.config import Settings
from coffeedesk.database import Database
from coffeedesk.repository import Repository
from coffeedesk.security import password_hash

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "testing/lab9/evidence"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="coffee-id-", dir="/tmp/opencode") as tmp:
        settings = Settings(db_path=Path(tmp) / "test.db", mode="test")
        database = Database(settings.db_path)
        database.initialize(demo=True)
        password = secrets.token_urlsafe(20)
        with database.transaction(write=True) as con:
            Repository(con).set_password(1, password_hash(password))
        body = {"title": "Проверка типа ID", "description": "JSON boolean не является целочисленным идентификатором бара.", "cafe_id": True, "category_id": 1}
        with TestClient(create_app(settings)) as client:
            auth = client.post("/auth/login", json={"username": "admin", "password": password})
            response = client.post("/requests", json=body, headers={"X-CSRF-Token": auth.json()["csrf_token"]})
        version = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        with database.transaction() as con:
            count = con.execute("SELECT COUNT(*) FROM Requests").fetchone()[0]
        record = {"version": version, "request": body, "expected_http": 422, "actual_http": response.status_code, "response": response.json(), "database_count": count, "result": "PASS" if response.status_code == 422 else "FAIL"}
        # Never overwrite the before-fix evidence during a later retest.
        suffix = "retest" if response.status_code == 422 else "before_fix"
        path = output / f"BUG-01_{suffix}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        log = f"POST /requests with cafe_id=true\nCommit: {version}\nExpected HTTP 422; actual HTTP {response.status_code}\nDatabase request count: {count}; expected 12\nResult: {record['result']}\nNo login credentials, CSRF or cookie values retained.\n"
        path.with_suffix(".txt").write_text(log)
        print(log)
        assert response.status_code == 422, f"Expected strict integer validation (422), got {response.status_code}; boolean coerced into cafe_id=1"


if __name__ == "__main__":
    main()

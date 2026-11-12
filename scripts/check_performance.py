"""Measure the exact local NFR-03 criterion; not a production SLA/load test."""

import json
import math
import platform
import time
from pathlib import Path

import httpx
from test_environment import isolated_server

from coffeedesk.database import Database
from coffeedesk.repository import Repository

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "testing/lab10/performance"
    with isolated_server(output) as (base, settings, credentials, _):
        database = Database(settings.db_path)
        with database.transaction(write=True) as con:
            repo = Repository(con)
            for number in range(988):
                repo.create_request({"title": f"Плановая проверка {number}", "description": "Обезличенная тестовая заявка для измерения списка на тысяче записей.", "cafe_id": number % 3 + 1, "category_id": number % 5 + 1, "applicant_id": 5, "priority": "normal"})
            assert con.execute("SELECT COUNT(*) FROM Requests").fetchone()[0] == 1000
        with httpx.Client(base_url=base) as client:
            assert client.post("/auth/login", json={"username": "admin", "password": credentials["admin"]}).status_code == 200
            timings = []
            for _ in range(30):
                start = time.perf_counter()
                response = client.get("/requests?limit=100")
                elapsed = (time.perf_counter() - start) * 1000
                assert response.status_code == 200 and len(response.json()) == 100
                timings.append(elapsed)
        p95 = sorted(timings)[math.ceil(.95 * len(timings)) - 1]
        result = {"criterion": "NFR-03", "database_rows": 1000, "http_requests": 30, "limit": 100, "method": "30 sequential localhost HTTP requests, nearest-rank p95, connection reused", "python": platform.python_version(), "timings_ms": timings, "p95_ms": p95, "threshold_ms": 1000, "result": "PASS" if p95 < 1000 else "FAIL", "scope": "This workstation only, not concurrent load or remote latency."}
        (output / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(f"NFR-03: 1000 rows, 30 real HTTP requests, p95={p95:.2f} ms <1000 ms: {result['result']}")
        assert p95 < 1000


if __name__ == "__main__":
    main()

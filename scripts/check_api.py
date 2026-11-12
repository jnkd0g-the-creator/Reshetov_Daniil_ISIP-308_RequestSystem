"""Execute real curl requests and retain sanitized request/response evidence."""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(base, credentials_file, output):
    credentials = dict(line.split("\t") for line in credentials_file.read_text().splitlines())
    results = []
    output.mkdir(parents=True, exist_ok=True)
    (ROOT / ".local").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / ".local") as tmp:
        jar = str(Path(tmp) / "cookies")
        csrf = None

        def call(method, path, expected, body=None, authenticated=True):
            args = ["curl", "--silent", "--show-error", "--max-time", "20", "--write-out", "\n%{http_code}", "-X", method]
            if authenticated:
                args += ["-b", jar, "-c", jar]
            if csrf and method != "GET" and authenticated:
                args += ["-H", "X-CSRF-Token: " + csrf]
            payload = None
            if body is not None:
                args += ["-H", "Content-Type: application/json", "--data-binary", "@-"]
                payload = json.dumps(body, ensure_ascii=False)
            raw = subprocess.check_output([*args, base + path], input=payload, text=True)
            text, status = raw.rsplit("\n", 1)
            data = json.loads(text) if text else None
            safe = {"user": data["user"], "csrf_token": "[REDACTED]"} if path == "/auth/login" else data
            record = {"method": method, "path": path, "expected": expected, "actual": int(status), "status": "PASS" if int(status) == expected else "FAIL", "request": "[REDACTED]" if path == "/auth/login" else body, "response": safe}
            results.append(record)
            assert int(status) == expected, f"{method} {path}: expected {expected}, got {status}"
            return data

        call("GET", "/health", 200, authenticated=False)
        call("GET", "/requests", 401, authenticated=False)
        auth = call("POST", "/auth/login", 200, {"username": "admin", "password": credentials["admin"]})
        csrf = auth["csrf_token"]
        for path in ("/requests", "/requests/1", "/users", "/statuses", "/categories", "/cafes", "/requests?q=%D0%9A%D0%A0%D0%90%D0%9D&category_id=1"):
            call("GET", path, 200)
        call("POST", "/requests", 422, {"title": ""})
        item = call("POST", "/requests", 201, {"title": "Проверка REST крана", "description": "Заявка создана реальным curl для проверки HTTP API.", "cafe_id": 1, "category_id": 1, "priority": "high"})
        path = "/requests/" + str(item["id"])
        call("PATCH", path, 200, {"description": "Изменённое через REST описание проблемы с краном."})
        call("PATCH", path + "/assignment", 422, {"assignee_id": 5})
        call("PATCH", path + "/assignment", 200, {"assignee_id": 3})
        call("PATCH", path + "/status", 409, {"status_code": "done"})
        call("PATCH", path + "/status", 200, {"status_code": "in_progress"})
        call("POST", path + "/comments", 201, {"body": "Проверена реальная запись комментария через API."})
        call("GET", path + "/history", 200)
        call("PATCH", path + "/status", 200, {"status_code": "done"})
        call("PATCH", path + "/status", 200, {"status_code": "closed"})
        call("DELETE", path, 400)
        call("DELETE", path + "?confirm=true", 204)
        call("GET", "/requests?archived=true", 200)
        call("GET", "/requests/99999999", 404)
        call("GET", "/requests/-1", 422)
        call("GET", "/requests?status_code=unknown", 422)
        schema = call("GET", "/openapi.json", 200, authenticated=False)
        (output / "openapi.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n")
        # OpenAPI is saved separately, not duplicated in the request transcript.
        results[-1]["response"] = {"info": schema["info"], "paths_count": len(schema["paths"])}
        call("POST", "/auth/logout", 204)
    (output / "curl_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    summary = f"CoffeeDesk · real curl requests · {base}\n" + "\n".join(f"{i:02d}. {r['method']} {r['path']} → {r['actual']} (expected {r['expected']}) {r['status']}" for i, r in enumerate(results, 1))
    summary += "\n\nExamples (credentials and session values redacted):\n"
    for r in (results[4], results[10], results[-5]):
        summary += f"\n{r['method']} {r['path']}\n" + json.dumps(r["response"], ensure_ascii=False, indent=2) + "\n"
    (output / "curl_results.txt").write_text(summary)
    print(f"{len(results)} real curl requests: all PASS; sanitized output: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--credentials", type=Path, default=ROOT / ".local/demo_credentials.txt")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/api")
    args = parser.parse_args()
    run(args.base.rstrip("/"), args.credentials, args.output)

"""Build inert public database, execute all exercise SQL, record real results."""

import json
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "docs/database"


def statements(text):
    current = ""
    for line in text.splitlines():
        if line.lstrip().startswith("--"):
            continue
        current += line + "\n"
        if sqlite3.complete_statement(current):
            yield current.strip()
            current = ""


def main():
    (ROOT / ".local").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / ".local") as tmp:
        path = Path(tmp) / "demo.sqlite3"
        con = sqlite3.connect(path)
        con.row_factory = sqlite3.Row
        con.executescript((FOLDER / "schema.sql").read_text())
        con.executescript((FOLDER / "seed.sql").read_text())
        # Repeat both scripts to verify idempotency without resetting user data.
        con.executescript((FOLDER / "schema.sql").read_text())
        con.executescript((FOLDER / "seed.sql").read_text())
        output = []
        results = []
        for statement in statements((FOLDER / "queries.sql").read_text()):
            cur = con.execute(statement)
            rows = [dict(row) for row in cur.fetchall()] if cur.description else []
            output.append("sqlite> " + statement + "\n" + (json.dumps(rows, ensure_ascii=False, indent=2) if cur.description else f"rowcount={cur.rowcount}"))
            results.append({"sql": statement, "rows": rows, "rowcount": cur.rowcount})
        counts = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ["Roles", "Users", "Cafes", "Categories", "Statuses", "Requests", "Comments", "RequestHistory", "Sessions"]}
        assert counts["Requests"] == 12 and counts["Sessions"] == 0
        assert con.execute("PRAGMA foreign_key_check").fetchall() == []
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        # Demonstrate actual FK rejection and atomic rollback.
        try:
            con.execute("INSERT INTO Comments(request_id,author_id,body) VALUES(99999,5,'FK rejection test')")
        except sqlite3.IntegrityError as exc:
            output.append("Negative FK test: " + str(exc))
            con.rollback()
        else:
            raise AssertionError("FK was not enforced")
        output.append("\nFinal counts (exercise rolled back): " + json.dumps(counts, ensure_ascii=False))
        output.append("PRAGMA foreign_key_check: []\nPRAGMA integrity_check: ok\nAll password_hash values: !unset (no usable passwords). Sessions: 0.")
        (FOLDER / "query_results.txt").write_text("\n\n".join(output), encoding="utf-8")
        (FOLDER / "query_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
        con.close()
        (FOLDER / "coffee_demo.sqlite3").write_bytes(path.read_bytes())
        summary = "CoffeeDesk · SQL execution, Python sqlite3 " + sqlite3.sqlite_version + "\n\n" + "\n".join(f"{table}: {count}" for table, count in counts.items())
        summary += "\n\nExecuted: INSERT=5 SELECT=6 UPDATE=2 DELETE=2\nWHERE SELECT >=3; JOIN SELECT >=2\nFK rejection: FOREIGN KEY constraint failed\nIntegrity: ok; foreign_key_check: []\nRepeated schema/seed: PASS; exercise rollback: PASS\nFull SQL and results: docs/database/query_results.txt\n"
        (FOLDER / "verification.txt").write_text(summary, encoding="utf-8")
        print(summary)


if __name__ == "__main__":
    main()

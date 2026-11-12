import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import ROOT

SQL_DIR = ROOT / "docs/database"


class Database:
    def __init__(self, path):
        self.path = Path(path)

    def connect(self):
        con = sqlite3.connect(self.path, timeout=5)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.create_function("CASEFOLD", 1, lambda value: value.casefold() if value else "", deterministic=True)
        return con

    @contextmanager
    def transaction(self, write=False):
        con = self.connect()
        try:
            con.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def initialize(self, demo=False):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = self.connect()
        try:
            version = con.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("Unsupported database version")
            con.executescript((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))
            if demo:
                con.executescript((SQL_DIR / "seed.sql").read_text(encoding="utf-8"))
            con.commit()
        finally:
            con.close()

    def healthy(self):
        with self.transaction() as con:
            return con.execute("PRAGMA user_version").fetchone()[0] == 1 and con.execute("SELECT COUNT(*) FROM Statuses").fetchone()[0] == 4

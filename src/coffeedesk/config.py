import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path("data/coffeedesk.db")
    mode: str = "development"
    port: int = 8000
    secure_cookies: bool = False
    session_seconds: int = 8 * 60 * 60

    @classmethod
    def from_env(cls):
        mode = os.getenv("COFFEE_MODE", "development")
        if mode not in {"development", "production", "test"}:
            raise ValueError("COFFEE_MODE must be development, production or test")
        secure = os.getenv("COFFEE_SECURE_COOKIES", "true" if mode == "production" else "false")
        if secure not in {"true", "false"}:
            raise ValueError("COFFEE_SECURE_COOKIES must be true or false")
        if mode == "production" and secure != "true":
            raise ValueError("Production requires Secure cookies and HTTPS")
        port = int(os.getenv("PORT", "8000"))
        if not 1 <= port <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
        return cls(Path(os.getenv("COFFEE_DB_PATH", "data/coffeedesk.db")), mode, port, secure == "true")

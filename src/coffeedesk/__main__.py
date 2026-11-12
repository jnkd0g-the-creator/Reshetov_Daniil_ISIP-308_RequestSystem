import argparse
import os
import secrets
from pathlib import Path

from .config import Settings
from .database import Database
from .repository import Repository
from .security import password_hash


def initialize_demo(settings, credentials_path=Path(".local/demo_credentials.txt")):
    database = Database(settings.db_path)
    database.initialize(demo=True)
    credentials = []
    with database.transaction(write=True) as con:
        repo = Repository(con)
        for user in repo.users():
            # Re-running initialization must not silently rotate working passwords.
            if repo.user_by_username(user["username"])["password_hash"] == "!unset":
                password = secrets.token_urlsafe(16)
                repo.set_password(user["id"], password_hash(password))
                credentials.append(f"{user['username']}\t{password}")
    if credentials:
        credentials_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(credentials_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as target:
            os.chmod(credentials_path, 0o600)
            target.write("\n".join(credentials) + "\n")
    print(f"Demo initialized: {settings.db_path}. Credentials stored locally: {credentials_path} (never commit).")


def main():
    parser = argparse.ArgumentParser(description="CoffeeDesk maintenance requests")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init-db", help="Initialize fictional demonstration data")
    init.add_argument("--demo", action="store_true", required=True)
    init.add_argument("--credentials", type=Path, default=Path(".local/demo_credentials.txt"))
    sub.add_parser("serve", help="Start one application worker")
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.command == "init-db":
        initialize_demo(settings, args.credentials)
    else:
        import uvicorn

        uvicorn.run("coffeedesk.app:create_app", factory=True, host="0.0.0.0", port=settings.port, workers=1)


if __name__ == "__main__":
    main()

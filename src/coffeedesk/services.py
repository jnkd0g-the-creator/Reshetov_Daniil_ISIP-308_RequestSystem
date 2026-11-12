"""Business policy. No FastAPI, HTML, or SQL in this layer."""

import hmac
import json
import secrets
import time
from collections import defaultdict, deque
from threading import Lock

from .errors import DomainError, forbidden, not_found
from .models import CommentCreate, RequestCreate, RequestUpdate
from .repository import Repository
from .security import password_hash, token_hash, verify_password

MANAGERS = {"admin", "operator"}
NEXT_STATUS = {"new": "in_progress", "in_progress": "done", "done": "closed"}


class RequestService:
    def __init__(self, database):
        self.database = database

    @staticmethod
    def _scope(user):
        if user["role_code"] in MANAGERS:
            return None
        return ("assignee_id" if user["role_code"] == "technician" else "applicant_id", user["id"])

    def _get(self, repo, user, request_id, modifying=False):
        item = repo.request(request_id)
        if not item:
            raise not_found()
        scope = self._scope(user)
        if scope and item[scope[0]] != scope[1]:
            raise not_found()
        if item["archived"] and (user["role_code"] != "admin" or modifying):
            raise not_found()
        return item

    @staticmethod
    def _references(repo, fields):
        for key in ("cafe_id", "category_id"):
            if key in fields and not repo.exists(key, fields[key]):
                raise DomainError("Указанный кофе-бар или категория не существует.")

    def list(self, user, **filters):
        if filters.get("archived") and user["role_code"] != "admin":
            raise forbidden()
        # Service callers get the same bounds as HTTP callers.
        if not 1 <= filters.get("limit", 100) <= 100 or filters.get("offset", 0) < 0:
            raise DomainError("Недопустимые параметры страницы.")
        with self.database.transaction() as con:
            return Repository(con).requests(scope=self._scope(user), **filters)

    def get(self, user, request_id):
        with self.database.transaction() as con:
            return self._get(Repository(con), user, request_id)

    def create(self, user, data):
        if user["role_code"] not in {"admin", "operator", "applicant"}:
            raise forbidden()
        fields = RequestCreate.model_validate(data).model_dump()
        fields["applicant_id"] = user["id"]
        with self.database.transaction(write=True) as con:
            repo = Repository(con)
            self._references(repo, fields)
            request_id = repo.create_request(fields)
            repo.add_history(request_id, user["id"], "created", new="new")
            return repo.request(request_id)

    def update(self, user, request_id, data):
        fields = RequestUpdate.model_validate(data).model_dump(exclude_unset=True)
        with self.database.transaction(write=True) as con:
            repo = Repository(con)
            item = self._get(repo, user, request_id, modifying=True)
            if user["role_code"] not in MANAGERS and not (user["role_code"] == "applicant" and item["status_code"] == "new"):
                raise forbidden()
            if item["status_code"] == "closed":
                raise DomainError("Закрытая заявка недоступна для редактирования.", 409, "state_conflict")
            self._references(repo, fields)
            changed = {key: value for key, value in fields.items() if item[key] != value}
            if changed:
                repo.update_request(request_id, changed)
                repo.add_history(request_id, user["id"], "updated", json.dumps({key: item[key] for key in changed}, ensure_ascii=False), json.dumps(changed, ensure_ascii=False))
            return repo.request(request_id)

    def assign(self, user, request_id, assignee_id):
        if user["role_code"] not in MANAGERS:
            raise forbidden()
        with self.database.transaction(write=True) as con:
            repo = Repository(con)
            item = self._get(repo, user, request_id, modifying=True)
            if item["status_code"] in {"done", "closed"}:
                raise DomainError("Нельзя переназначить выполненную или закрытую заявку.", 409, "state_conflict")
            if assignee_id is None:
                if item["status_code"] != "new":
                    raise DomainError("Нельзя снять исполнителя у заявки в работе.", 409, "state_conflict")
            else:
                assignee = repo.user(assignee_id)
                if not assignee or not assignee["active"] or assignee["role_code"] != "technician":
                    raise DomainError("Выберите действующего пользователя роли «Исполнитель».")
            if item["assignee_id"] != assignee_id:
                repo.update_request(request_id, {"assignee_id": assignee_id})
                repo.add_history(request_id, user["id"], "assigned", str(item["assignee_id"]), str(assignee_id))
            return repo.request(request_id)

    def change_status(self, user, request_id, status):
        with self.database.transaction(write=True) as con:
            repo = Repository(con)
            item = self._get(repo, user, request_id, modifying=True)
            role = user["role_code"]
            if role not in MANAGERS and role != "technician":
                raise forbidden()
            if role == "technician" and status == "closed":
                raise forbidden()
            if status == item["status_code"]:
                return item
            if NEXT_STATUS.get(item["status_code"]) != status:
                raise DomainError("Допустим только следующий статус: Новая → В работе → Выполнена → Закрыта.", 409, "state_conflict")
            if status == "in_progress" and item["assignee_id"] is None:
                raise DomainError("Сначала назначьте исполнителя.", 409, "state_conflict")
            repo.update_request(request_id, {"status_code": status})
            repo.add_history(request_id, user["id"], "status_changed", item["status_code"], status)
            return repo.request(request_id)

    def archive(self, user, request_id, confirmed=False):
        if user["role_code"] != "admin":
            raise forbidden()
        if not confirmed:
            raise DomainError("Подтвердите архивацию заявки.", 400, "confirmation_required")
        with self.database.transaction(write=True) as con:
            repo = Repository(con)
            item = self._get(repo, user, request_id)
            if item["archived"]:
                return
            if item["status_code"] != "closed":
                raise DomainError("Архивировать можно только закрытую заявку.", 409, "state_conflict")
            repo.update_request(request_id, {"archived": 1})
            repo.add_history(request_id, user["id"], "archived", "false", "true")

    def comments(self, user, request_id):
        with self.database.transaction() as con:
            repo = Repository(con)
            self._get(repo, user, request_id)
            return repo.comments(request_id)

    def add_comment(self, user, request_id, data):
        fields = CommentCreate.model_validate(data)
        with self.database.transaction(write=True) as con:
            repo = Repository(con)
            self._get(repo, user, request_id, modifying=True)
            return repo.add_comment(request_id, user["id"], fields.body)

    def history(self, user, request_id):
        with self.database.transaction() as con:
            repo = Repository(con)
            self._get(repo, user, request_id)
            return repo.history(request_id)

    def users(self, user):
        with self.database.transaction() as con:
            return Repository(con).users(user["id"] if user["role_code"] == "applicant" else None)

    def catalog(self, name):
        with self.database.transaction() as con:
            return Repository(con).catalog(name)


class AuthService:
    def __init__(self, database, session_seconds=28800):
        self.database = database
        self.session_seconds = session_seconds
        self.dummy_hash = password_hash(secrets.token_urlsafe(24))
        self.failures = defaultdict(deque)
        self.lock = Lock()

    def login(self, username, password):
        current = int(time.time())
        # Bounded fixed-size buckets avoid retaining arbitrary attempted usernames.
        bucket = int(token_hash(username)[:6], 16) % 1024
        with self.lock:
            attempts = self.failures[bucket]
            while attempts and attempts[0] < current - 300:
                attempts.popleft()
            if len(attempts) >= 10:
                raise DomainError("Слишком много попыток. Повторите через 5 минут.", 429, "rate_limited")
            attempts.append(current)
        with self.database.transaction() as con:
            user = Repository(con).user_by_username(username)
        stored = user["password_hash"] if user and user["password_hash"].startswith("pbkdf2_") else self.dummy_hash
        valid = verify_password(password, stored)
        if not user or not user["active"] or not valid:
            raise DomainError("Неверный логин или пароль.", 401, "unauthenticated")
        with self.lock:
            self.failures.pop(bucket, None)
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self.database.transaction(write=True) as con:
            repo = Repository(con)
            repo.add_session(token_hash(token), token_hash(csrf), user["id"], current + self.session_seconds, current)
            public = repo.user(user["id"])
        return public, token, csrf

    def authenticate(self, token, csrf=None, modifying=False):
        if not token or len(token) > 128:
            raise DomainError("Необходимо войти в систему.", 401, "unauthenticated")
        with self.database.transaction() as con:
            repo = Repository(con)
            session = repo.session(token_hash(token))
            if not session or session["expires_at"] <= int(time.time()):
                raise DomainError("Сессия истекла. Войдите снова.", 401, "unauthenticated")
            user = repo.user(session["user_id"])
            if not user or not user["active"]:
                raise DomainError("Необходимо войти в систему.", 401, "unauthenticated")
            if modifying and (not csrf or not hmac.compare_digest(token_hash(csrf), session["csrf_hash"])):
                raise DomainError("Не удалось подтвердить запрос. Войдите снова.", 403, "csrf_failed")
            return user

    def logout(self, token):
        with self.database.transaction(write=True) as con:
            Repository(con).delete_session(token_hash(token))

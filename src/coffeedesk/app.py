import sqlite3
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from . import __version__
from .api import router
from .config import Settings
from .database import Database
from .errors import DomainError
from .services import AuthService, RequestService

STATIC = Path(__file__).parent / "static"


def error(status, code, message, details=None):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details or []}})


def create_app(settings=None):
    settings = settings or Settings.from_env()
    app = FastAPI(title="CoffeeDesk API", version=__version__, description="Учёт эксплуатационных заявок кофе-баров. Все данные учебные. Требуется cookie-сессия; для изменений передайте X-CSRF-Token из ответа входа.")
    app.state.settings = settings
    app.state.database = Database(settings.db_path)
    app.state.service = RequestService(app.state.database)
    app.state.auth = AuthService(app.state.database, settings.session_seconds)
    # Lab 6 web controllers. Lab 7 exposes the same service adapters publicly.
    app.include_router(router, prefix="/ui-api", include_in_schema=False)

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return error(exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Do not echo submitted passwords, request bodies or exception objects.
        details = [{"field": ".".join(str(x) for x in item["loc"]), "type": item["type"]} for item in exc.errors()]
        return error(422, "validation_error", "Проверьте обязательные поля, длину и допустимые значения.", details)

    @app.exception_handler(sqlite3.Error)
    async def database_error(request, exc):
        return error(503, "database_unavailable", "База данных временно недоступна. Повторите запрос позже.")

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error(exc.status_code, "http_error", "Ресурс или метод недоступен.")

    @app.middleware("http")
    async def response_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if not request.url.path.startswith("/assets"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/health", tags=["Служебные"], summary="Проверить приложение и БД")
    def health():
        if not app.state.database.healthy():
            return error(503, "database_unavailable", "База данных не инициализирована.")
        return {"status": "ok", "database": "ok", "version": __version__}

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/assets", StaticFiles(directory=STATIC), name="assets")
    return app

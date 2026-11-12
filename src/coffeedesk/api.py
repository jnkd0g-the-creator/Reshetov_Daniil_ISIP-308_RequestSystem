"""Thin HTTP adapters; all role and workflow decisions live in services."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response, Security
from fastapi.security import APIKeyCookie

from .models import (
    Assignment, CafeOut, CategoryOut, CommentCreate, CommentOut, HistoryOut,
    Login, LoginOut, RequestCreate, RequestOut, RequestUpdate, StatusOut, StatusUpdate, UserOut,
)

router = APIRouter()
RequestId = Annotated[int, Path(gt=0, description="Положительный идентификатор заявки")]
session_cookie = APIKeyCookie(name="coffee_session", auto_error=False, description="Сессия из POST /auth/login; не публикуйте значение cookie.")


def current_user(
    request: Request,
    token: Annotated[str | None, Security(session_cookie)],
    csrf: Annotated[str | None, Header(alias="X-CSRF-Token", description="Для изменения данных: csrf_token из ответа входа")] = None,
):
    return request.app.state.auth.authenticate(
        token,
        csrf,
        modifying=request.method not in {"GET", "HEAD", "OPTIONS"},
    )


User = Annotated[dict, Depends(current_user)]


@router.post("/auth/login", response_model=LoginOut, tags=["Авторизация"], summary="Войти в систему")
def login(data: Login, request: Request, response: Response):
    user, token, csrf = request.app.state.auth.login(data.username, data.password)
    settings = request.app.state.settings
    response.set_cookie("coffee_session", token, httponly=True, samesite="lax", secure=settings.secure_cookies, max_age=settings.session_seconds, path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"user": user, "csrf_token": csrf}


@router.get("/auth/me", response_model=UserOut, tags=["Авторизация"], summary="Текущий пользователь")
def me(user: User):
    return user


@router.post("/auth/logout", status_code=204, tags=["Авторизация"], summary="Завершить сессию")
def logout(request: Request, user: User):
    request.app.state.auth.logout(request.cookies["coffee_session"])
    response = Response(status_code=204)
    response.delete_cookie("coffee_session", path="/")
    return response


@router.get("/requests", response_model=list[RequestOut], tags=["Заявки"], summary="Доступные заявки, поиск и совместные фильтры")
def requests(
    request: Request, user: User,
    q: Annotated[str, Query(max_length=120, description="Номер, тема или описание, без учёта регистра")] = "",
    status_code: Literal["new", "in_progress", "done", "closed"] | None = None,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    cafe_id: Annotated[int | None, Query(gt=0)] = None,
    archived: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return request.app.state.service.list(user, q=q.strip(), status_code=status_code, category_id=category_id, cafe_id=cafe_id, archived=archived, limit=limit, offset=offset)


@router.get("/requests/{request_id}", response_model=RequestOut, tags=["Заявки"], summary="Карточка заявки по ID")
def get_request(request_id: RequestId, request: Request, user: User):
    return request.app.state.service.get(user, request_id)


@router.post("/requests", response_model=RequestOut, status_code=201, tags=["Заявки"], summary="Создать новую заявку")
def create_request(data: RequestCreate, request: Request, user: User, response: Response):
    item = request.app.state.service.create(user, data)
    response.headers["Location"] = f"{request.scope.get('root_path', '')}/requests/{item['id']}"
    return item


@router.patch("/requests/{request_id}", response_model=RequestOut, tags=["Заявки"], summary="Частично изменить реквизиты")
def update_request(request_id: RequestId, data: RequestUpdate, request: Request, user: User):
    return request.app.state.service.update(user, request_id, data)


@router.patch("/requests/{request_id}/assignment", response_model=RequestOut, tags=["Заявки"], summary="Назначить или снять исполнителя")
def assign(request_id: RequestId, data: Assignment, request: Request, user: User):
    return request.app.state.service.assign(user, request_id, data.assignee_id)


@router.patch("/requests/{request_id}/status", response_model=RequestOut, tags=["Заявки"], summary="Перейти к следующему статусу")
def status(request_id: RequestId, data: StatusUpdate, request: Request, user: User):
    return request.app.state.service.change_status(user, request_id, data.status_code)


@router.delete("/requests/{request_id}", status_code=204, tags=["Заявки"], summary="Архивировать закрытую заявку (admin)")
def archive(request_id: RequestId, request: Request, user: User, confirm: Annotated[bool, Query(description="Явное подтверждение архивации")] = False):
    request.app.state.service.archive(user, request_id, confirmed=confirm)
    return Response(status_code=204)


@router.get("/requests/{request_id}/comments", response_model=list[CommentOut], tags=["Обсуждение"], summary="Комментарии заявки")
def comments(request_id: RequestId, request: Request, user: User):
    return request.app.state.service.comments(user, request_id)


@router.post("/requests/{request_id}/comments", response_model=CommentOut, status_code=201, tags=["Обсуждение"], summary="Добавить комментарий")
def add_comment(request_id: RequestId, data: CommentCreate, request: Request, user: User):
    return request.app.state.service.add_comment(user, request_id, data)


@router.get("/requests/{request_id}/history", response_model=list[HistoryOut], tags=["Обсуждение"], summary="История изменений")
def history(request_id: RequestId, request: Request, user: User):
    return request.app.state.service.history(user, request_id)


@router.get("/users", response_model=list[UserOut], tags=["Справочники"], summary="Публичные данные разрешённых пользователей")
def users(request: Request, user: User):
    return request.app.state.service.users(user)


@router.get("/statuses", response_model=list[StatusOut], tags=["Справочники"], summary="Четыре статуса")
def statuses(request: Request, user: User):
    return request.app.state.service.catalog("statuses")


@router.get("/categories", response_model=list[CategoryOut], tags=["Справочники"], summary="Категории неисправностей")
def categories(request: Request, user: User):
    return request.app.state.service.catalog("categories")


@router.get("/cafes", response_model=list[CafeOut], tags=["Справочники"], summary="Кофе-бары")
def cafes(request: Request, user: User):
    return request.app.state.service.catalog("cafes")

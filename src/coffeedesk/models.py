from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=120)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=4000)]
CommentBody = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Priority = Literal["low", "normal", "high", "urgent"]
Status = Literal["new", "in_progress", "done", "closed"]
PositiveId = Annotated[int, Field(gt=0, strict=True)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RequestCreate(Input):
    title: Title
    description: Description
    cafe_id: PositiveId
    category_id: PositiveId
    priority: Priority = "normal"


class RequestUpdate(Input):
    title: Title | None = None
    description: Description | None = None
    cafe_id: PositiveId | None = None
    category_id: PositiveId | None = None
    priority: Priority | None = None

    @model_validator(mode="after")
    def no_explicit_null(self):
        if any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError("Изменяемое поле не может быть null.")
        if not self.model_fields_set:
            raise ValueError("Укажите хотя бы одно поле.")
        return self


class StatusUpdate(Input):
    status_code: Status


class Assignment(Input):
    assignee_id: PositiveId | None


class CommentCreate(Input):
    body: CommentBody


class Login(Input):
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50)]
    password: Annotated[str, StringConstraints(min_length=1, max_length=200)]


class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role_code: str
    active: bool


class LoginOut(BaseModel):
    user: UserOut
    csrf_token: str


class CategoryOut(BaseModel):
    id: int
    name: str


class CafeOut(CategoryOut):
    address: str


class StatusOut(BaseModel):
    code: str
    name: str
    sort_order: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict]


class ErrorOut(BaseModel):
    error: ErrorDetail


class RequestOut(BaseModel):
    id: int
    number: str
    title: str
    description: str
    cafe_id: int
    category_id: int
    status_code: str
    applicant_id: int
    assignee_id: int | None
    priority: str
    archived: bool
    created_at: str
    updated_at: str
    cafe_name: str
    category_name: str
    status_name: str
    applicant_name: str
    assignee_name: str | None


class CommentOut(BaseModel):
    id: int
    request_id: int
    author_id: int
    author_name: str
    body: str
    created_at: str


class HistoryOut(BaseModel):
    id: int
    request_id: int
    actor_id: int
    actor_name: str
    event: str
    old_value: str | None
    new_value: str | None
    created_at: str

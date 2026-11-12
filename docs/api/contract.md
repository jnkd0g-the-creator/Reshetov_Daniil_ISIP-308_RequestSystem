# REST-контракт CoffeeDesk (ЛР7)

API размещён в корне: `/requests`, не только `/ui-api` интерфейса ЛР6.
FastAPI адаптирует HTTP к существующим сервисам без повторения бизнес-логики.
JSON UTF-8; ID положительный. POST создаёт, PATCH частично меняет,
DELETE **архивирует**, а не физически удаляет. PUT не реализован: методичка
допускает PUT/PATCH, выбран PATCH с запретом пустого объекта и явного null.

## Авторизация

POST `/auth/login`: `{username, password}` → HttpOnly cookie `coffee_session`,
`{user, csrf_token}`. Для всех изменений, кроме входа, заголовок
`X-CSRF-Token` из этого ответа обязателен. GET `/auth/me` → текущий пользователь;
POST `/auth/logout` → 204 и удаление сессии. Срок сессии 8 часов.
Пароли, cookie и csrf_token в примерах ответов доказательств редактируются.
GET `/health` открыт; справочники и заявки требуют входа.

| Метод | Путь | Вход/параметры | Успех | Ошибки |
|---|---|---|---|---|
| GET | /requests | q, status_code, category_id, cafe_id, archived, limit 1–100, offset ≥0 | 200, массив | 401, 403, 422, 503 |
| GET | /requests/{id} | id >0 | 200, карточка | 401, 404, 422 |
| POST | /requests | title, description, cafe_id, category_id, priority | 201 + Location | 401, 403, 422 |
| PATCH | /requests/{id} | хотя бы одно изменяемое поле | 200 | 401, 403, 404, 409, 422 |
| DELETE | /requests/{id} | confirm=true, admin, closed | 204 без тела | 400, 401, 403, 404, 409 |
| PATCH | /requests/{id}/assignment | assignee_id положительный или null | 200 | 401, 403, 404, 409, 422 |
| PATCH | /requests/{id}/status | status_code из 4 значений | 200 | 401, 403, 404, 409, 422 |
| GET/POST | /requests/{id}/comments | POST body 1–2000 | 200/201 | 401, 403, 404, 422 |
| GET | /requests/{id}/history | id | 200 | 401, 404 |
| GET | /users | публичные поля; заявителю только он сам | 200, массив | 401 |
| GET | /statuses | — | 200, массив | 401 |
| GET | /categories | — | 200, массив | 401 |
| GET | /cafes | — | 200, массив | 401 |

Все БД-операции могут дать 503. Единый формат ошибки:
`{"error":{"code":"validation_error","message":"…","details":[{"field":"body.title","type":"string_too_short"}]}}`.
Ошибка не отражает пароль, SQL или трассировку. Недоступная по scope заявка
даёт тот же 404, что и несуществующая: это не раскрывает чужие объекты.

## JSON-схемы

RequestCreate: тема после trim 3–120, описание 10–4000, существующие положительные
ID бара/категории, priority low/normal/high/urgent. Автор/статус/номер/дата
назначаются сервером, extra поля запрещены. RequestUpdate: те же поля optional,
но переданный null запрещён, пустой PATCH — 422. Assignee null допустим только
в отдельном контракте назначения. Выходные схемы не включают секретные поля.

Фактические JSON-схемы всех входов и выходов: `openapi.json`, доступны на
`/openapi.json`. Swagger `/docs`; на POST login пароль не следует включать
в скриншоты. В Swagger для изменения скопируйте csrf_token локально в поле
X-CSRF-Token; публикация/видеозапись этого значения не нужна.

## Принято после критического ревью ИИ

1. Архив требует отдельного confirm, а не обычного DELETE без защиты.
2. Все mutation-запросы проверяют CSRF и серверные роли.
3. PATCH null не означает случайное обнуление обязательного поля.
4. Неправомерное чтение скрывается 404; UserOut не содержит hash/session.
5. Ошибка нормализована, Pydantic input не включается в JSON.

Повторяемая curl-проверка: `python scripts/check_api.py --base http://127.0.0.1:8000`.
Использует только локальный файл demo_credentials; подтверждения сохранены
в `curl_results.json/txt`, без секретных значений. `curl_examples.sh` — коллекция
для самостоятельного безопасного запуска.

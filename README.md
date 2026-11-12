# CoffeeDesk — заявки кофе-баров

Учебный проект Решетова Даниила, ИСИП-308, по дисциплине
«Технологии разработки программного обеспечения».

Система регистрирует неисправности в кофе-барах: протекающий кран,
поломку кофемашины, проблемы с электрикой, мебелью и хозяйственными работами.
Заявитель сообщает о проблеме, оператор назначает исполнителя, исполнитель
отмечает выполнение, оператор или администратор закрывает заявку.

Стек: **Python 3.10**, FastAPI, SQLite, HTML/CSS/JavaScript, pytest, Docker.
Python 3.10 и существующее `.venv` выбраны по прямому указанию заказчика
(в методичке Python 3.12+ рекомендован, а не обязателен).

## Материалы

- `tasks/` — исходные задания, без изменений.
- `docs/TZ.md` — техническое задание.
- `docs/architecture/` — архитектура и диаграммы.
- `docs/prototype/` — самостоятельный интерактивный прототип, 5 экранов.
- `docs/database/` — ER-модель, SQL и учебная SQLite-база.
- `docs/reports/` — отчёты лабораторных №1–10 в DOCX.
- `docs/ai_log.md` — журнал использования ИИ.
- `testing/lab9/`, `testing/lab10/` — результаты проверок.

## Локальный запуск (Python 3.10)

Из корня проекта, Linux/macOS:

```bash
python3.10 -m venv .venv  # только при первом запуске, существующее не пересоздавать
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
python -m coffeedesk init-db --demo
python -m coffeedesk serve
```

Windows: `py -3.10 -m venv .venv`, затем `.venv\Scripts\activate`;
остальные команды такие же. Приложение: http://localhost:8000.

Вход: логины `admin`, `operator`, `tech1`, `tech2`, `barista1`, `barista2`.
Уникальные случайные пароли сохранены **только локально** в
`.local/demo_credentials.txt` (формат: логин, табуляция, пароль; доступ 0600).
Откройте файл локально, не включайте его в Git, скриншоты или видео.
Повторный `init-db --demo` не удаляет данные и не меняет уже заданные пароли.
Потерянный файл с паролями не восстанавливается из хешей.

Данные учебные. Рабочая SQLite: `data/coffeedesk.db`, не публикуется.
Остановить сервер: Ctrl+C. Перезапуск сохраняет заявки.
Для отдельной чистой среды задайте `COFFEE_DB_PATH=.local/another.db` перед
инициализацией и запуском; не удаляйте рабочую базу.

## Основные сценарии

1. Войти заявителем, создать заявку о кране, выбрать бар и категорию.
2. Оператором назначить tech1/tech2, начать работу.
3. Исполнителем оставить комментарий, отметить выполнение.
4. Оператором принять результат и закрыть.
5. Администратором подтвердить архив закрытой заявки.

Поиск работает по номеру/теме/описанию без учёта регистра кириллицы;
фильтры статуса/категории/бара применяются совместно. Заявитель видит свои,
исполнитель — назначенные. Редактирование и все права проверяются сервером.

## Проверка

```bash
python -m pytest tests -q
python scripts/run_tests.py  # весь набор: 57 проверок, полный лог + coverage
ruff check src tests
```

Тесты используют временные БД, не трогают рабочие записи. Полная инструкция:
[`testing/lab10/README.md`](testing/lab10/README.md). Фактический прогон:
**57 PASS, покрытие строк Python 90,38%**. Браузерный набор ЛР9:
`python scripts/run_lab9.py` (требует Chromium/Playwright), **30 PASS**;
это автоматизация, а не самостоятельный ручной прогон студентом.

## Ход выполнения

План и соответствие методичке: [`docs/assignment_checklist.md`](docs/assignment_checklist.md).
Недоступные внешние действия отмечены явно, без выдуманных результатов.

## REST API

Тот же сервер, базовый адрес `http://localhost:8000`.
Swagger: `/docs`, машиночитаемая схема: `/openapi.json`.
Основные методы: `GET/POST /requests`, `GET/PATCH/DELETE /requests/{id}`,
`GET /users`, `/statuses`, `/categories`, `/cafes`.
`PATCH /requests/{id}/assignment` назначает, `/status` меняет статус.
Удаление — подтверждённый архив закрытой, `DELETE ...?confirm=true` (admin).

API требует входа: `POST /auth/login` устанавливает cookie; ответ содержит
`csrf_token`, необходимый в `X-CSRF-Token` для изменений. Не публикуйте
ответ входа. Пример открытого запроса и запрос без авторизации:

```bash
curl http://localhost:8000/health
curl -i http://localhost:8000/requests  # ожидается 401
python scripts/check_api.py          # 29 реальных curl, локальные demo credentials
```

Полный контракт, таблица endpoints, коллекция curl и реальные обезличенные
ответы: [`docs/api/`](docs/api/). `GET /requests` возвращает JSON-массив;
поиск `q=КРАН`, фильтры `status_code=new&category_id=1`, limit/offset.

## Docker и повторный деплой

```bash
cp .env.example .env
docker compose build
docker compose run --rm coffee python -m coffeedesk init-db --demo --credentials /app/data/demo_credentials.txt
docker compose up -d --wait
curl http://127.0.0.1:8000/health
```

При занятом порте задайте `PORT=8001` в локальном `.env`.
База сохраняется в именованном томе. `down -v` удаляет данные — не выполнять
для обычного обновления. Контейнер работает от UID 10001, имеет healthcheck.
Подробная инструкция с нуля, настройки, резервирование и шаги сервера:
[`docs/deployment/README.md`](docs/deployment/README.md).

**Фактически проверен локальный Docker на `http://127.0.0.1:8001`** (Compose
project `coffeedesk-labs`). Удалённый деплой пока BLOCKED: сервер/адрес не задан.
Не выдаём localhost за внешний стенд. Для production нужны TLS и Secure-cookie.

## Сдача лабораторных

- [10 DOCX-отчётов](docs/reports/README.md), с собственными диаграммами/скриншотами проекта.
- [Итоговый отчёт о качестве](testing/lab10/test_summary.md), [трассировка ТЗ](docs/acceptance_matrix.md).
- [30 заполненных кейсов](testing/lab9/test_cases.csv), [реальные дефекты и retest](testing/lab9/bug_reports.md).
- [Единый AI-журнал](docs/ai_log.md): модель, полные подзапросы, результаты/проверки/решения, без приписывания действий студенту.
- [MP4 технической репетиции и план записи](docs/demo/README.md), реальный продукт/HTTP/pytest, **без голоса**.

**Для полного закрытия методички ещё нужны:** согласованный внешний сервер
(ЛР8), самостоятельное прохождение ручных кейсов студентом (ЛР9) и финальное
видео ≤5 минут с его голосовым комментарием (ЛР10). Эти пункты честно BLOCKED,
не выданы за выполненные. Готовая программная часть доступна локально.

Репозиторий: https://github.com/jnkd0g-the-creator/Reshetov_Daniil_ISIP-308_RequestSystem

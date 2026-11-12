# Повторяемый запуск и деплой CoffeeDesk (ЛР8)

## 1. Чистый локальный Python

Команды в основном README. Проверено в **новом venv** с установкой зависимостей,
новой SQLite и настоящим HTTP-процессом: `clean_start.txt`.
Воспроизведение: `python scripts/clean_start.py` (Linux, /tmp/opencode).
Не использует и не удаляет пользовательскую базу.

## 2. Docker на своей машине

Требуется Docker Engine + Compose v2. Из корня клонированного репозитория:

```bash
git clone https://github.com/jnkd0g-the-creator/Reshetov_Daniil_ISIP-308_RequestSystem.git
cd Reshetov_Daniil_ISIP-308_RequestSystem
git switch develop  # после финального merge допустим main
cp .env.example .env
# Если Python-сервер занимает 8000, задайте PORT=8001 в локальном .env.
docker compose --progress plain build
docker compose run --rm coffee python -m coffeedesk init-db --demo --credentials /app/data/demo_credentials.txt
docker compose up -d --wait
docker compose ps
curl http://127.0.0.1:8000/health
```

В браузере http://127.0.0.1:8000 (или выбранный PORT).
Чтобы прочитать пароль **только локально**, используйте
`docker compose exec coffee cat /app/data/demo_credentials.txt` без записи экрана
и без публикации вывода. Логины такие же, как при Python-запуске, но пароли
сгенерированы отдельно. Не показывайте файл в видео.

Выполненный агентом стенд имеет отдельный Compose project `coffeedesk-labs`
и PORT=8001, чтобы не занять Python-порт. Повторить его:
`python scripts/docker_evidence.py`. Журнал `docker_run.txt` доказывает
non-root UID 10001, health, HTTP и сохранение заявки при **пересоздании** контейнера.

SQLite и закрытый файл паролей находятся в именованном томе `coffee_data`.
`docker compose down` останавливает сервис и сохраняет том.
**Не используйте `down -v`** без сознательного решения удалить все данные.
Обновление: `git pull --ff-only`, `docker compose build`, `docker compose up -d --wait`.
Схема версии 1 создаётся командой init-db; для будущих изменений нужны миграции,
автоматического изменения существующих таблиц нет.

Резервная копия живой БД: выполнять SQLite `Connection.backup` в контейнере,
не копировать частично записанный файл. Перед обновлением сделайте backup;
rollback приложения не должен автоматически удалять данные.

## 3. Удалённая среда — инструкция, не выполненный деплой

**Фактический статус: BLOCKED.** Заказчик не указал согласованный SSH-хост,
учебный сервер или внешний URL. 127.0.0.1 текущей машины не называется удалённым
адресом. Локальный Docker не засчитывается как проверенный внешний деплой.
Пароли/ключи в чат или Git не передавать: настроить SSH локально и сообщить alias.

На согласованном сервере с Docker:

1. Подключиться через настроенный SSH, клонировать репозиторий, выбрать main/develop.
2. Подготовить `.env`, `COFFEE_MODE=production`, `COFFEE_SECURE_COOKIES=true`.
3. Оставить приложение на 127.0.0.1; установить TLS reverse proxy Caddy/Nginx
   на согласованном домене. Не открывать учебный HTTP-порт в Интернет.
4. Выполнить build, init-db и up; получить тестовый пароль вне Git.
5. Через HTTPS проверить `/health`, `/docs`, вход, список, создание и ошибку 422.
6. Проверить сохранение после recreate и отсутствие секретов в логах.
7. Записать URL, дату, среду/версию и внешние проверки в `deployment_status.json`.
8. Добавить реальные скриншоты удалённого UI/health/API; затем сменить BLOCKED на PASS.

Сеть, DNS, TLS, серверная стоимость и права требуют согласования.
Платные облачные ресурсы без разрешения не создавались.

## 4. Настройки

| env | Назначение | По умолчанию |
|---|---|---|
| COFFEE_MODE | development/test/production | development |
| COFFEE_DB_PATH | путь SQLite (эквивалент строки подключения) | data/coffeedesk.db; compose /app/data/coffeedesk.db |
| COFFEE_SECURE_COOKIES | cookie только HTTPS | false, production требует true |
| PORT | порт процесса и compose | 8000 |
| COFFEE_BIND | интерфейс публикации Docker | 127.0.0.1 |

Python читает переменные ОС, **не загружает .env сам**; Compose читает `.env`.
Для Python используйте `export COFFEE_DB_PATH=...` (PowerShell `$env:...`).
Секретного ключа нет: сессия — 256-битный случайный токен, в SQLite только SHA256.
Python 3.10 согласован заказчиком; обновление до поддерживаемой версии требуется
перед долгосрочным промышленным использованием.

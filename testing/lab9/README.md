# ЛР9 · материалы и воспроизведение

- `test_plan.md` — объект, версия, область, виды и критерии.
- `test_cases.csv` — 30 кейсов, UTF-8 BOM, разделитель `;`; открывается Excel/LibreOffice.
  Каждый содержит ID/цель/предусловия/шаги/данные/ожидание/факт/статус/evidence.
- `environment.json` — действительная версия и хеш исходников, временный URL.
- `results.md/json` — результаты последнего полного инструментального прогона.
- `evidence/TC-*.json/png` — доказательства по каждому кейсу; для HTTP скриншот
  показывает сохранённый реальный ответ, для UI — непосредственно браузер.
- `bug_reports.md` — BUG-01 продукта и отдельно TEST-01 тестового ожидания.
- `initial_failure/` — сохранённый исходный сбой теста и версия, не заменённые PASS.
- `api/curl_results.*` — 29 реальных curl на той же изолированной версии.
- `http_results.json`, `server.txt` — дополнительный HTTP/серверный журнал без секретов.

```bash
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
python -m playwright install chromium
# Ubuntu/Debian: при необходимости python -m playwright install-deps chromium
python scripts/run_lab9.py
```

На исходной Ubuntu 26.04 Playwright 1.55 не распознаёт platform. Использован
fallback `PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64`; три недостающие
библиотеки libnspr4/libnss3/libasound2t64 распакованы без root в
`/tmp/opencode/browser-libs`. `scripts/browser_support.py` подхватывает этот
локальный workaround, если каталог существует; на поддерживаемой ОС он не нужен.
Это ограничение стенда, не ошибка приложения. Сервер и рабочая БД не нужны:
скрипт поднимает временный процесс/SQLite и после прогона очищает собственные данные.

Результат агента: **30 PASS / 0 FAIL**. Это **не** самостоятельные ручные действия
студента. `execution_mode` явно указан, все `manual_status=BLOCKED` до личного
повторения. Порядок завершения ручной части — `manual_review.md`.
Не менять исходный FAIL в отчёте: после исправления добавлять retest.
